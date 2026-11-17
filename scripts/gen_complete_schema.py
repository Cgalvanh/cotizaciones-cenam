import csv
import os

areas_file = "c:/Users/cgalvan/Documents/antigravity/jolly-galileo/nube_segura/data/areas_tecnicas.csv"
catalog_file = "c:/Users/cgalvan/Documents/antigravity/jolly-galileo/nube_segura/data/catalogo_servicios.csv"

def sql_escape(val):
    if val is None:
        return "NULL"
    s = str(val).replace("'", "''")
    return f"'{s}'"

schema_head = """-- ========================================================
-- Esquema Completo de Base de Datos PostgreSQL para Supabase
-- Sistema de Cotizaciones y DSNR PR - CENAM
-- ========================================================

-- 1. Extensiones necesarias
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Limpieza limpia para permitir re-ejecución (idempotencia)
DROP TABLE IF EXISTS bitacora_auditoria CASCADE;
DROP TABLE IF EXISTS consultas_especialistas CASCADE;
DROP TABLE IF EXISTS partidas CASCADE;
DROP TABLE IF EXISTS sub_solicitudes_at CASCADE;
DROP TABLE IF EXISTS solicitudes_master CASCADE;
DROP TABLE IF EXISTS catalogo_servicios CASCADE;
DROP TABLE IF EXISTS areas_tecnicas CASCADE;
DROP TABLE IF EXISTS usuarios CASCADE;

-- 2. Tabla de Áreas Técnicas
CREATE TABLE areas_tecnicas (
    clave TEXT PRIMARY KEY,
    nombre TEXT NOT NULL
);

-- 3. Catálogo Oficial de Servicios Metrológicos
CREATE TABLE catalogo_servicios (
    clave_servicio TEXT PRIMARY KEY,
    clave_area TEXT NOT NULL REFERENCES areas_tecnicas (clave) ON DELETE CASCADE,
    nombre_tramite TEXT,
    supuesto TEXT NOT NULL,
    alcance TEXT,
    observaciones TEXT,
    costo NUMERIC(12,2) NOT NULL,
    fundamento_juridico TEXT,
    es_in_situ TEXT DEFAULT 'NO',
    dias_habiles_defecto INTEGER DEFAULT 5
);

-- 4. Tabla de Usuarios y Roles (RBAC)
CREATE TABLE usuarios (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    correo TEXT UNIQUE NOT NULL,
    nombre_completo TEXT NOT NULL,
    rol TEXT NOT NULL CHECK (rol IN ('SSI', 'AT', 'ADMIN')),
    clave_area TEXT REFERENCES areas_tecnicas (clave) ON DELETE SET NULL,
    password_hash TEXT NOT NULL,
    activo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 5. Solicitudes Master (Expediente General)
CREATE TABLE solicitudes_master (
    id BIGSERIAL PRIMARY KEY,
    no_solicitud TEXT UNIQUE NOT NULL,
    no_folio TEXT UNIQUE NOT NULL,
    no_cotizacion TEXT,
    version INTEGER DEFAULT 1,
    cliente TEXT NOT NULL,
    representante TEXT,
    telefono TEXT,
    correo TEXT,
    rfc TEXT,
    pais TEXT DEFAULT 'México',
    es_extranjero BOOLEAN DEFAULT FALSE,
    aplica_iva BOOLEAN DEFAULT TRUE,
    fecha_recepcion TIMESTAMPTZ DEFAULT NOW(),
    fecha_emision DATE,
    vigencia DATE,
    estado TEXT DEFAULT 'TURNADA' CHECK (estado IN ('NUEVA', 'TURNADA', 'CONSOLIDADA', 'EMITIDA', 'CANCELADA')),
    es_in_situ BOOLEAN DEFAULT FALSE
);

-- 6. Sub-solicitudes asignadas a cada Área Técnica
CREATE TABLE sub_solicitudes_at (
    id BIGSERIAL PRIMARY KEY,
    solicitud_id BIGINT NOT NULL REFERENCES solicitudes_master (id) ON DELETE CASCADE,
    clave_area TEXT NOT NULL REFERENCES areas_tecnicas (clave) ON DELETE CASCADE,
    estado TEXT DEFAULT 'ASIGNADA' CHECK (estado IN ('ASIGNADA', 'EN_CONSULTA', 'DEVUELTA', 'COMPLETADA')),
    motivo_devolucion TEXT,
    area_sugerida TEXT,
    fecha_asignacion TIMESTAMPTZ DEFAULT NOW(),
    fecha_limite_sla DATE NOT NULL
);

-- 7. Partidas (Equipos a Calibrar)
CREATE TABLE partidas (
    id BIGSERIAL PRIMARY KEY,
    sub_solicitud_id BIGINT REFERENCES sub_solicitudes_at (id) ON DELETE SET NULL,
    solicitud_id BIGINT NOT NULL REFERENCES solicitudes_master (id) ON DELETE CASCADE,
    numero_partida INTEGER NOT NULL,
    descripcion_equipo TEXT NOT NULL,
    marca TEXT,
    modelo TEXT,
    no_serie TEXT,
    id_interno TEXT,
    alcance_solicitado TEXT,
    es_manual BOOLEAN DEFAULT FALSE,
    clave_servicio TEXT,
    descripcion_servicio TEXT,
    tiempo_dias_habiles INTEGER DEFAULT 5,
    cantidad INTEGER DEFAULT 1,
    precio_unitario NUMERIC(12,2) DEFAULT 0.00,
    precio_total NUMERIC(12,2) DEFAULT 0.00,
    es_no_realizable BOOLEAN DEFAULT FALSE,
    motivo_dsnr TEXT
);

-- 8. Bitácora de Consultas a Especialistas (Evidencia ISO 17025)
CREATE TABLE consultas_especialistas (
    id BIGSERIAL PRIMARY KEY,
    sub_solicitud_id BIGINT NOT NULL REFERENCES sub_solicitudes_at (id) ON DELETE CASCADE,
    especialista_nombre TEXT NOT NULL,
    pregunta TEXT NOT NULL,
    respuesta TEXT,
    fecha_consulta TIMESTAMPTZ DEFAULT NOW(),
    fecha_respuesta TIMESTAMPTZ,
    estado TEXT DEFAULT 'PENDIENTE' CHECK (estado IN ('PENDIENTE', 'CONTESTADA', 'REASIGNADA'))
);

-- 9. Bitácora de Auditoría Inmutable
CREATE TABLE bitacora_auditoria (
    id BIGSERIAL PRIMARY KEY,
    usuario_correo TEXT NOT NULL,
    accion TEXT NOT NULL,
    entidad TEXT NOT NULL,
    registro_id TEXT,
    detalles JSONB,
    fecha TIMESTAMPTZ DEFAULT NOW()
);

-- Índices de Rendimiento
CREATE INDEX idx_sub_sol_area ON sub_solicitudes_at(clave_area);
CREATE INDEX idx_partidas_sol ON partidas(solicitud_id);
CREATE INDEX idx_partidas_sub ON partidas(sub_solicitud_id);
CREATE INDEX idx_cat_area ON catalogo_servicios(clave_area);

-- Habilitar Row Level Security (RLS)
ALTER TABLE solicitudes_master ENABLE ROW LEVEL SECURITY;
ALTER TABLE sub_solicitudes_at ENABLE ROW LEVEL SECURITY;
ALTER TABLE partidas ENABLE ROW LEVEL SECURITY;
ALTER TABLE consultas_especialistas ENABLE ROW LEVEL SECURITY;
ALTER TABLE bitacora_auditoria ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Acceso total solicitudes_master" ON solicitudes_master FOR ALL USING (true);
CREATE POLICY "Acceso total sub_solicitudes_at" ON sub_solicitudes_at FOR ALL USING (true);
CREATE POLICY "Acceso total partidas" ON partidas FOR ALL USING (true);
CREATE POLICY "Acceso total consultas_especialistas" ON consultas_especialistas FOR ALL USING (true);
CREATE POLICY "Acceso total bitacora_auditoria" ON bitacora_auditoria FOR ALL USING (true);

-- ========================================================
-- DATOS INICIALES (SEED DATA)
-- ========================================================

"""

# Read areas
areas_sql = "-- Inserción de Áreas Técnicas\nINSERT INTO areas_tecnicas (clave, nombre) VALUES\n"
area_rows = []
with open(areas_file, "r", encoding="utf-8") as f:
    for r in csv.DictReader(f):
        c = sql_escape(r['Clave'].strip())
        n = sql_escape(r['Nombre'].strip())
        area_rows.append(f"({c}, {n})")
areas_sql += ",\n".join(area_rows) + ";\n\n"

# Users
users_sql = """-- Inserción de Usuarios Iniciales
-- Contraseña por defecto para todos: Cenam2026* (Hash SHA-256 + salt institucional)
INSERT INTO usuarios (correo, nombre_completo, rol, clave_area, password_hash, activo) VALUES
('ssi@cenam.mx', 'Ventanilla Central SSI', 'SSI', NULL, '68e1c6b12e604f86be2e8f1766a50352ef29b8705a81ca04ae98f7e340a6b57d', true),
('admin@cenam.mx', 'Administrador de Sistemas', 'ADMIN', NULL, '68e1c6b12e604f86be2e8f1766a50352ef29b8705a81ca04ae98f7e340a6b57d', true),
('at.dimensional@cenam.mx', 'Ing. Roberto Nava (AT Dimensional)', 'AT', 'AT-01', '68e1c6b12e604f86be2e8f1766a50352ef29b8705a81ca04ae98f7e340a6b57d', true),
('at.electrica@cenam.mx', 'Ing. Laura Méndez (AT Eléctrica)', 'AT', 'AT-02', '68e1c6b12e604f86be2e8f1766a50352ef29b8705a81ca04ae98f7e340a6b57d', true),
('at.radiofrecuencia@cenam.mx', 'Ing. Carlos Vega (AT Radiofrecuencia)', 'AT', 'AT-03', '68e1c6b12e604f86be2e8f1766a50352ef29b8705a81ca04ae98f7e340a6b57d', true),
('at.tiempo@cenam.mx', 'Dra. Patricia Cruz (AT Tiempo)', 'AT', 'AT-04', '68e1c6b12e604f86be2e8f1766a50352ef29b8705a81ca04ae98f7e340a6b57d', true),
('at.temperatura@cenam.mx', 'M. en C. Luis Morales (AT Termometría)', 'AT', 'AT-05', '68e1c6b12e604f86be2e8f1766a50352ef29b8705a81ca04ae98f7e340a6b57d', true),
('at.optica@cenam.mx', 'Ing. Daniel Flores (AT Óptica)', 'AT', 'AT-06', '68e1c6b12e604f86be2e8f1766a50352ef29b8705a81ca04ae98f7e340a6b57d', true),
('at.masa@cenam.mx', 'Ing. Sandra Rangel (AT Masa)', 'AT', 'AT-07', '68e1c6b12e604f86be2e8f1766a50352ef29b8705a81ca04ae98f7e340a6b57d', true),
('at.presion@cenam.mx', 'Ing. Jorge Salinas (AT Presión)', 'AT', 'AT-08', '68e1c6b12e604f86be2e8f1766a50352ef29b8705a81ca04ae98f7e340a6b57d', true),
('at.flujo@cenam.mx', 'M. en C. Elena Torres (AT Flujo)', 'AT', 'AT-09', '68e1c6b12e604f86be2e8f1766a50352ef29b8705a81ca04ae98f7e340a6b57d', true),
('at.acustica@cenam.mx', 'Ing. Fernando Rios (AT Acústica)', 'AT', 'AT-10', '68e1c6b12e604f86be2e8f1766a50352ef29b8705a81ca04ae98f7e340a6b57d', true),
('at.dureza@cenam.mx', 'Ing. Marco Soto (AT Dureza)', 'AT', 'AT-11', '68e1c6b12e604f86be2e8f1766a50352ef29b8705a81ca04ae98f7e340a6b57d', true),
('at.quimica@cenam.mx', 'Dra. Carmen Beltrán (AT Química)', 'AT', 'AT-12', '68e1c6b12e604f86be2e8f1766a50352ef29b8705a81ca04ae98f7e340a6b57d', true),
('at.fisicoquimica@cenam.mx', 'Dr. Alejandro Luna (AT Fisicoquímica)', 'AT', 'AT-13', '68e1c6b12e604f86be2e8f1766a50352ef29b8705a81ca04ae98f7e340a6b57d', true),
('at.insitu@cenam.mx', 'Ing. Héctor Ortiz (AT Servicios In Situ)', 'AT', 'AT-14', '68e1c6b12e604f86be2e8f1766a50352ef29b8705a81ca04ae98f7e340a6b57d', true);

"""

# Catalog
cat_sql = "-- Inserción del Catálogo de Servicios Oficiales\nINSERT INTO catalogo_servicios (clave_servicio, clave_area, nombre_tramite, supuesto, alcance, observaciones, costo, fundamento_juridico, es_in_situ, dias_habiles_defecto) VALUES\n"
cat_rows = []
with open(catalog_file, "r", encoding="utf-8") as f:
    for r in csv.DictReader(f):
        cs = sql_escape(r['Clave_Servicio'])
        ca = sql_escape(r['Clave_Area'])
        nt = sql_escape(r['Nombre_Tramite'])
        sup = sql_escape(r['Supuesto'])
        alc = sql_escape(r['Alcance'])
        obs = sql_escape(r['Observaciones'])
        costo = r['Costo']
        fund = sql_escape(r['Fundamento_Juridico'])
        insitu = sql_escape(r['Es_In_Situ'])
        dias = r['Dias_Habiles_Defecto']
        cat_rows.append(f"({cs}, {ca}, {nt}, {sup}, {alc}, {obs}, {costo}, {fund}, {insitu}, {dias})")

cat_sql += ",\n".join(cat_rows) + ";\n"

full_sql = schema_head + areas_sql + users_sql + cat_sql

out_sql_file = "c:/Users/cgalvan/Documents/antigravity/jolly-galileo/nube_segura/supabase_schema.sql"
with open(out_sql_file, "w", encoding="utf-8") as f:
    f.write(full_sql)

print(f"Generated complete schema with seed data: {len(full_sql)} characters written to {out_sql_file}")
