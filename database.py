import sqlite3
import csv
import os
import re
import hashlib
import random
import uuid
from datetime import datetime, timedelta

DB_PATH = os.path.abspath("cotizaciones_cenam.db")
DATA_DIR = os.path.abspath("data")


def hash_password(password: str) -> str:
    salt = "cenam_secure_salt_2026"
    return hashlib.sha256((password + salt).encode("utf-8")).hexdigest()

def verify_credentials(correo, password):
    conn = get_connection()
    c = conn.cursor()
    pwd_hash = hash_password(password)
    c.execute("SELECT id, correo, nombre_completo, rol, clave_area, activo FROM usuarios WHERE LOWER(correo) = ? AND password_hash = ?", (correo.strip().lower(), pwd_hash))
    user = c.fetchone()
    conn.close()
    if user and user['activo']:
        return dict(user)
    return None

def get_usuarios_list():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id, correo, nombre_completo, rol, clave_area FROM usuarios WHERE activo = 1 ORDER BY rol DESC, clave_area ASC")
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    c = conn.cursor()
    
    # Enable foreign keys
    c.execute("PRAGMA foreign_keys = ON;")

    # 0. Usuarios y Autenticacion
    c.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id TEXT PRIMARY KEY,
        correo TEXT UNIQUE NOT NULL,
        nombre_completo TEXT NOT NULL,
        rol TEXT NOT NULL,
        clave_area TEXT,
        password_hash TEXT NOT NULL,
        activo INTEGER DEFAULT 1
    );
    """)

    
    # 1. Areas Tecnicas
    c.execute("""
    CREATE TABLE IF NOT EXISTS areas_tecnicas (
        clave TEXT PRIMARY KEY,
        nombre TEXT NOT NULL,
        id_area TEXT,
        direccion TEXT
    );
    """)
    
    # 2. Catalogo de Servicios
    c.execute("""
    CREATE TABLE IF NOT EXISTS catalogo_servicios (
        clave_servicio TEXT PRIMARY KEY,
        clave_area TEXT NOT NULL,
        nombre_tramite TEXT,
        supuesto TEXT NOT NULL,
        alcance TEXT,
        observaciones TEXT,
        costo REAL NOT NULL,
        fundamento_juridico TEXT,
        es_in_situ TEXT DEFAULT 'NO',
        dias_habiles_defecto INTEGER DEFAULT 5,
        FOREIGN KEY (clave_area) REFERENCES areas_tecnicas (clave)
    );
    """)
    
    # 3. Solicitudes Master
    c.execute("""
    CREATE TABLE IF NOT EXISTS solicitudes_master (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        no_solicitud TEXT UNIQUE NOT NULL,
        no_folio TEXT NOT NULL,
        no_cotizacion TEXT,
        version INTEGER DEFAULT 1,
        cliente TEXT NOT NULL,
        representante TEXT,
        telefono TEXT,
        correo TEXT,
        rfc TEXT,
        pais TEXT DEFAULT 'México',
        es_extranjero INTEGER DEFAULT 0,
        aplica_iva INTEGER DEFAULT 1,
        fecha_recepcion TEXT NOT NULL,
        fecha_emision TEXT,
        vigencia TEXT,
        estado TEXT DEFAULT 'TURNADA',
        es_in_situ INTEGER DEFAULT 0,
        representante_legal_cenam TEXT,
        vigencia_programacion TEXT DEFAULT '3 semanas',
        modalidad_retorno TEXT,
        direccion_servicio_sitio TEXT,
        condiciones_acceso_planta TEXT,
        fecha_aceptacion_cotizacion TEXT,
        fecha_confirmacion_programa TEXT
    );
    """)
    
    # 4. Sub-solicitudes asignadas a ATs
    c.execute("""
    CREATE TABLE IF NOT EXISTS sub_solicitudes_at (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        solicitud_id INTEGER NOT NULL,
        clave_area TEXT NOT NULL,
        estado TEXT DEFAULT 'ASIGNADA',
        motivo_devolucion TEXT,
        area_sugerida TEXT,
        fecha_asignacion TEXT NOT NULL,
        fecha_limite_sla TEXT NOT NULL,
        fecha_recepcion_prog TEXT,
        fecha_inicio_prog TEXT,
        fecha_entrega_prog TEXT,
        fecha_limite_prog TEXT,
        motivo_reprogramacion TEXT,
        FOREIGN KEY (solicitud_id) REFERENCES solicitudes_master (id) ON DELETE CASCADE,
        FOREIGN KEY (clave_area) REFERENCES areas_tecnicas (clave)
    );
    """)
    
    # 5. Partidas
    c.execute("""
    CREATE TABLE IF NOT EXISTS partidas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sub_solicitud_id INTEGER,
        solicitud_id INTEGER NOT NULL,
        numero_partida INTEGER NOT NULL,
        descripcion_equipo TEXT NOT NULL,
        marca TEXT,
        modelo TEXT,
        no_serie TEXT,
        id_interno TEXT,
        alcance_solicitado TEXT,
        certificado_anterior TEXT,
        magnitud TEXT,
        exactitud_clase TEXT,
        condiciones_particulares TEXT,
        es_manual INTEGER DEFAULT 0,
        clave_servicio TEXT,
        descripcion_servicio TEXT,
        tiempo_dias_habiles INTEGER DEFAULT 5,
        cantidad INTEGER DEFAULT 1,
        precio_unitario REAL DEFAULT 0.0,
        precio_total REAL DEFAULT 0.0,
        es_no_realizable INTEGER DEFAULT 0,
        motivo_dsnr TEXT,
        aceptada_cliente INTEGER DEFAULT 1,
        fecha_recepcion_equipo TEXT,
        fecha_inicio_calibracion TEXT,
        fecha_fin_calibracion TEXT,
        fecha_entrega_equipo TEXT,
        fecha_entrega_resultados TEXT,
        fecha_limite_aceptacion TEXT,
        FOREIGN KEY (sub_solicitud_id) REFERENCES sub_solicitudes_at (id) ON DELETE SET NULL,
        FOREIGN KEY (solicitud_id) REFERENCES solicitudes_master (id) ON DELETE CASCADE
    );
    """)
    
    # 6. Consultas a Especialistas
    c.execute("""
    CREATE TABLE IF NOT EXISTS consultas_especialistas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sub_solicitud_id INTEGER NOT NULL,
        especialista_nombre TEXT NOT NULL,
        pregunta TEXT NOT NULL,
        respuesta TEXT,
        fecha_consulta TEXT NOT NULL,
        fecha_respuesta TEXT,
        estado TEXT DEFAULT 'PENDIENTE',
        FOREIGN KEY (sub_solicitud_id) REFERENCES sub_solicitudes_at (id) ON DELETE CASCADE
    );
    """)
    
    conn.commit()
    
    # Migraciones para agregar columnas si la base de datos ya existía
    def add_col_if_missing(table, col_name, col_type):
        c.execute(f"PRAGMA table_info({table});")
        cols = [r[1] for r in c.fetchall()]
        if col_name not in cols:
            try:
                c.execute(f"ALTER TABLE {table} ADD COLUMN {col_name} {col_type};")
            except Exception:
                pass

    # Columnas en solicitudes_master
    add_col_if_missing("solicitudes_master", "representante_legal_cenam", "TEXT")
    add_col_if_missing("solicitudes_master", "vigencia_programacion", "TEXT DEFAULT '3 semanas'")
    add_col_if_missing("solicitudes_master", "modalidad_retorno", "TEXT")
    add_col_if_missing("solicitudes_master", "direccion_servicio_sitio", "TEXT")
    add_col_if_missing("solicitudes_master", "condiciones_acceso_planta", "TEXT")
    add_col_if_missing("solicitudes_master", "fecha_aceptacion_cotizacion", "TEXT")
    add_col_if_missing("solicitudes_master", "fecha_confirmacion_programa", "TEXT")
    add_col_if_missing("solicitudes_master", "orden_compra_cliente", "TEXT")
    add_col_if_missing("solicitudes_master", "token_seguimiento", "TEXT")
    add_col_if_missing("solicitudes_master", "no_orden_compra", "TEXT")
    add_col_if_missing("solicitudes_master", "orden_compra_pdf", "TEXT")
    add_col_if_missing("solicitudes_master", "fecha_aceptacion_cliente", "TEXT")
    add_col_if_missing("solicitudes_master", "partidas_aceptadas_json", "TEXT")
    add_col_if_missing("solicitudes_master", "origen", "TEXT DEFAULT 'SSI'")

    # Tabla de codigos OTP para acceso seguro del cliente
    c.execute("""
    CREATE TABLE IF NOT EXISTS codigos_otp (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        correo TEXT NOT NULL,
        codigo_hash TEXT NOT NULL,
        expiracion TEXT NOT NULL,
        usado INTEGER DEFAULT 0,
        creado_en TEXT NOT NULL
    );
    """)

    # Tabla de auditoria
    c.execute("""
    CREATE TABLE IF NOT EXISTS bitacora_auditoria (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_correo TEXT NOT NULL,
        accion TEXT NOT NULL,
        entidad TEXT NOT NULL,
        registro_id TEXT,
        detalles TEXT,
        fecha TEXT NOT NULL
    );
    """)

    # Columnas en sub_solicitudes_at
    add_col_if_missing("sub_solicitudes_at", "fecha_recepcion_prog", "TEXT")
    add_col_if_missing("sub_solicitudes_at", "fecha_inicio_prog", "TEXT")
    add_col_if_missing("sub_solicitudes_at", "fecha_entrega_prog", "TEXT")
    add_col_if_missing("sub_solicitudes_at", "fecha_limite_prog", "TEXT")
    add_col_if_missing("sub_solicitudes_at", "motivo_reprogramacion", "TEXT")

    # Columnas en partidas
    add_col_if_missing("partidas", "certificado_anterior", "TEXT")
    add_col_if_missing("partidas", "magnitud", "TEXT")
    add_col_if_missing("partidas", "exactitud_clase", "TEXT")
    add_col_if_missing("partidas", "condiciones_particulares", "TEXT")
    add_col_if_missing("partidas", "aceptada_cliente", "INTEGER DEFAULT 1")
    add_col_if_missing("partidas", "fecha_recepcion_equipo", "TEXT")
    add_col_if_missing("partidas", "fecha_inicio_calibracion", "TEXT")
    add_col_if_missing("partidas", "fecha_fin_calibracion", "TEXT")
    add_col_if_missing("partidas", "fecha_entrega_equipo", "TEXT")
    add_col_if_missing("partidas", "fecha_entrega_resultados", "TEXT")
    add_col_if_missing("partidas", "fecha_limite_aceptacion", "TEXT")
    add_col_if_missing("partidas", "comentarios_ssi", "TEXT")
    add_col_if_missing("partidas", "comentarios_cliente", "TEXT")
    add_col_if_missing("partidas", "estado_partida", "TEXT DEFAULT 'COTIZADA'")

    # Columnas en areas_tecnicas
    add_col_if_missing("areas_tecnicas", "id_area", "TEXT")
    add_col_if_missing("areas_tecnicas", "direccion", "TEXT")

    conn.commit()
    conn.close()
    load_seed_data()

def load_seed_data():
    conn = get_connection()
    c = conn.cursor()
    
    # 1. Cargar Areas Tecnicas si vacio o refrescar
    areas_path = os.path.join(DATA_DIR, "areas_tecnicas.csv")
    if os.path.exists(areas_path):
        with open(areas_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                clave = (row.get('clave') or row.get('codigo') or row.get('Clave') or '').strip()
                nombre = (row.get('nombre') or row.get('division_oficial') or row.get('Nombre') or '').strip()
                id_area = (row.get('id_area') or '').strip()
                direccion = (row.get('direccion') or row.get('direccion_general') or '').strip()
                if clave:
                    c.execute("""
                    INSERT OR REPLACE INTO areas_tecnicas (clave, nombre, id_area, direccion)
                    VALUES (?, ?, ?, ?)
                    """, (clave, nombre, id_area, direccion))
                
    # 2. Cargar Catalogo de Servicios si vacio
    c.execute("SELECT COUNT(*) FROM catalogo_servicios")
    count = c.fetchone()[0]
    cat_path = os.path.join(DATA_DIR, "catalogo_servicios.csv")
    if count == 0 and os.path.exists(cat_path):
        with open(cat_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                clave_serv = (row.get('Clave_Servicio') or row.get('clave_servicio') or '').strip()
                clave_area = (row.get('Clave_Area') or row.get('clave_area') or '').strip()
                if not clave_serv:
                    continue
                try:
                    costo_val = float(row.get('Costo') or row.get('costo') or row.get('precio') or 0.0)
                except ValueError:
                    costo_val = 0.0
                try:
                    dias_val = int(row.get('Dias_Habiles_Defecto') or row.get('dias_habiles_defecto') or 5)
                except ValueError:
                    dias_val = 5
                c.execute("""
                INSERT INTO catalogo_servicios (
                    clave_servicio, clave_area, nombre_tramite, supuesto,
                    alcance, observaciones, costo, fundamento_juridico,
                    es_in_situ, dias_habiles_defecto
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    clave_serv, clave_area,
                    row.get('Nombre_Tramite') or row.get('nombre_tramite') or '',
                    row.get('Supuesto') or row.get('supuesto') or row.get('descripcion') or '',
                    row.get('Alcance') or row.get('alcance') or '',
                    row.get('Observaciones') or row.get('observaciones') or '',
                    costo_val,
                    row.get('Fundamento_Juridico') or row.get('fundamento_juridico') or '',
                    row.get('Es_In_Situ') or row.get('es_in_situ') or 'NO',
                    dias_val
                ))
                
    
    # 3. Cargar Usuarios oficiales
    c.execute("SELECT COUNT(*) FROM usuarios")
    if c.fetchone()[0] == 0:
        pwd = hash_password("Cenam2026*")
        usuarios_default = [
            ("usr_ssi", "ssi@cenam.mx", "Ventanilla Central SSI", "SSI", None, pwd),
            ("usr_admin", "admin@cenam.mx", "Administrador General", "ADMIN", None, pwd),
            ("usr_410", "at410@cenam.mx", "410 - Mediciones Electromagnéticas", "AT", "410", pwd),
            ("usr_420", "at420@cenam.mx", "420 - Termometría", "AT", "420", pwd),
            ("usr_430", "at430@cenam.mx", "430 - Tiempo y Frecuencia", "AT", "430", pwd),
            ("usr_440", "at440@cenam.mx", "440 - Radiofrecuencias", "AT", "440", pwd),
            ("usr_510", "at510@cenam.mx", "510 - Vibraciones y Acústica", "AT", "510", pwd),
            ("usr_520", "at520@cenam.mx", "520 - Óptica y Radiometría", "AT", "520", pwd),
            ("usr_610", "at610@cenam.mx", "610 - Mat. Metálicos y Cerámicos", "AT", "610", pwd),
            ("usr_620", "at620@cenam.mx", "620 - Materiales Inorgánicos", "AT", "620", pwd),
            ("usr_630", "at630@cenam.mx", "630 - Materiales Orgánicos", "AT", "630", pwd),
            ("usr_700", "at700@cenam.mx", "700 - Metrología Mecánica", "AT", "700", pwd),
            ("usr_710", "at710@cenam.mx", "710 - Flujo y Volumen", "AT", "710", pwd),
            ("usr_720", "at720@cenam.mx", "720 - Fuerza y Presión", "AT", "720", pwd),
            ("usr_730", "at730@cenam.mx", "730 - Masa y Densidad", "AT", "730", pwd),
            ("usr_740", "at740@cenam.mx", "740 - Metrología Dimensional", "AT", "740", pwd),
            ("usr_810", "at810@cenam.mx", "810 - Servicios Tecnológicos", "AT", "810", pwd),
            ("usr_dim_alt", "at.dimensional@cenam.mx", "740 - Metrología Dimensional", "AT", "740", pwd),
            ("usr_elec_alt", "at.electrica@cenam.mx", "410 - Mediciones Electromagnéticas", "AT", "410", pwd),
            ("usr_temp_alt", "at.temperatura@cenam.mx", "420 - Termometría", "AT", "420", pwd),
            ("usr_pres_alt", "at.presion@cenam.mx", "720 - Fuerza y Presión", "AT", "720", pwd),
            ("usr_masa_alt", "at.masa@cenam.mx", "730 - Masa y Densidad", "AT", "730", pwd),
        ]
        for u in usuarios_default:
            c.execute("""
                INSERT OR IGNORE INTO usuarios (id, correo, nombre_completo, rol, clave_area, password_hash, activo)
                VALUES (?, ?, ?, ?, ?, ?, 1)
            """, u)

    conn.commit()
    conn.close()

def log_auditoria(usuario_correo, accion, entidad, registro_id, detalles):
    try:
        conn = get_connection()
        c = conn.cursor()
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute("""
            INSERT INTO bitacora_auditoria (usuario_correo, accion, entidad, registro_id, detalles, fecha)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (usuario_correo, accion, entidad, str(registro_id), str(detalles), now_str))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error logging audit trail: {e}")

# Consecutivos Institucionales Oficiales con Sufijo PR
def get_next_solicitud_numbers(count=1):
    """Genera una lista de N números consecutivos de solicitud con formato YYYY###PR."""
    year = datetime.now().year
    try:
        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT no_solicitud FROM solicitudes_master ORDER BY id DESC")
        rows = c.fetchall()
        conn.close()
        
        max_num = 0
        for r in rows:
            val = str(r['no_solicitud'] or '')
            m = re.search(r"(\d+)(?:PR)?$", val, re.IGNORECASE)
            if m:
                try:
                    digits = m.group(1)
                    seq = int(digits[-3:])
                    if seq > max_num:
                        max_num = seq
                except ValueError:
                    pass
                    
        return [f"{year}{(max_num + i):03d}PR" for i in range(1, count + 1)]
    except Exception as e:
        print(f"Advertencia calculando números de solicitud: {e}")
        return [f"{year}{i:03d}PR" for i in range(1, count + 1)]

def get_next_solicitud_number():
    return get_next_solicitud_numbers(1)[0]

def get_next_folio_number():
    """Genera consecutivo exacto: 4 dígitos + año + sufijo PR (ej. 0001-2026PR, 0010-2026PR)."""
    year = datetime.now().year
    try:
        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT no_folio FROM solicitudes_master ORDER BY id DESC")
        rows = c.fetchall()
        conn.close()
        
        max_num = 0
        for r in rows:
            val = str(r['no_folio'] or '')
            # Formato 0009-2026PR o 231-2026
            m = re.search(r"^(\d+)-", val)
            if m:
                try:
                    seq = int(m.group(1))
                    if seq > max_num:
                        max_num = seq
                except ValueError:
                    pass
                    
        next_seq = max_num + 1
        return f"{next_seq:04d}-{year}PR"
    except Exception as e:
        print(f"Advertencia calculando número de folio: {e}")
        return f"0001-{year}PR"

def get_next_cotizacion_number():
    """Genera consecutivo exacto: año (2 dígitos) + 4 dígitos + sufijo PR (ej. 260001PR, 260545PR)."""
    conn = get_connection()
    c = conn.cursor()
    year_prefix = datetime.now().year % 100
    c.execute("SELECT no_cotizacion FROM solicitudes_master WHERE no_cotizacion IS NOT NULL ORDER BY id DESC")
    rows = c.fetchall()
    conn.close()
    
    max_num = 0
    for r in rows:
        val = str(r['no_cotizacion'] or '')
        m = re.search(r"(\d+)(?:PR)?$", val, re.IGNORECASE)
        if m:
            try:
                digits = m.group(1)
                seq = int(digits[-4:])
                if seq > max_num:
                    max_num = seq
            except ValueError:
                pass
                
    next_seq = max_num + 1
    return f"{year_prefix:02d}{next_seq:04d}PR"

# Funciones de Cálculo de Días Hábiles
def restar_dias_habiles(fecha_dt, n_dias=2):
    """Calcula n días hábiles antes de una fecha dada (excluyendo sábados y domingos)."""
    curr = fecha_dt
    dias_restados = 0
    while dias_restados < n_dias:
        curr -= timedelta(days=1)
        if curr.weekday() < 5: # Lunes a Viernes
            dias_restados += 1
    return curr

def sumar_dias_habiles(fecha_dt, n_dias):
    """Calcula n días hábiles después de una fecha dada (excluyendo sábados y domingos)."""
    curr = fecha_dt
    dias_sumados = 0
    while dias_sumados < n_dias:
        curr += timedelta(days=1)
        if curr.weekday() < 5:
            dias_sumados += 1
    return curr

def get_areas_tecnicas():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT clave, nombre, id_area, direccion FROM areas_tecnicas ORDER BY clave")
    rows = c.fetchall()
    conn.close()
    return [{"clave": r["clave"], "nombre": r["nombre"], "id_area": r["id_area"], "direccion": r["direccion"]} for r in rows]

def get_servicios_por_area(clave_area):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT clave_servicio, supuesto, alcance, observaciones, costo, dias_habiles_defecto, es_in_situ,
               codigo_laboratorio, nombre_laboratorio, codigo_division, metodo, incertidumbre
        FROM catalogo_servicios
        WHERE clave_area = ?
        ORDER BY codigo_laboratorio, clave_servicio
    """, (clave_area,))
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def crear_expediente_y_solicitudes(cliente_data, items_list=None, user_correo="ssi@cenam.mx", **kwargs):
    """
    Alternativa 3 (Modelo Híbrido CENAM):
    A partir de la recepción en SSI, genera:
    1. UN SOLO Folio maestro (no_folio: XXXX-YYYYPR) para trazabilidad del expediente cliente.
    2. Agrupa los instrumentos por (clave_area, es_in_situ).
    3. Asigna un número de solicitud independiente (no_solicitud: YYYY###PR) a cada grupo.
    4. Registra cada solicitud en solicitudes_master, sub_solicitudes_at y sus partidas correspondientes.
    """
    if "usuario_correo" in kwargs:
        user_correo = kwargs["usuario_correo"]
    if isinstance(cliente_data, str):
        cliente_data = {
            "cliente": cliente_data,
            "representante": "",
            "telefono": "",
            "correo": "",
            "rfc": "",
            "pais": "México",
            "es_extranjero": 0,
            "aplica_iva": 1
        }
    elif items_list is None and isinstance(cliente_data, dict):
        items_list = cliente_data.get("instrumentos") or cliente_data.get("partidas") or cliente_data.get("items") or []
        cliente_data = {
            "cliente": cliente_data.get("cliente") or cliente_data.get("empresa") or "Cliente Desconocido",
            "representante": cliente_data.get("representante") or cliente_data.get("contacto") or "",
            "telefono": cliente_data.get("telefono") or "",
            "correo": cliente_data.get("correo") or "",
            "rfc": cliente_data.get("rfc") or "",
            "pais": cliente_data.get("pais") or "México",
            "es_extranjero": cliente_data.get("es_extranjero", 0),
            "aplica_iva": cliente_data.get("aplica_iva", 1)
        }

    if not items_list:
        # Si no hay lista explícita, crear una partida genérica para permitir la captura técnica
        items_list = [{
            "desc": "Instrumento de calibración / Calibración solicitada",
            "clave_area": "740",
            "es_in_situ": 0
        }]

    from collections import defaultdict
    grupos = defaultdict(list)
    for it in items_list:
        area = str(it.get("clave_area") or it.get("area") or "740")
        in_situ = 1 if (it.get("es_in_situ") in [1, "1", True, "SI", "SÍ", "True"]) else 0
        grupos[(area, in_situ)].append(it)

    no_folio = get_next_folio_number()
    num_solicitudes = len(grupos)
    solicitud_numbers = get_next_solicitud_numbers(num_solicitudes)

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    hoy_str = datetime.now().strftime("%Y-%m-%d")
    vig_str = f"{datetime.now().year}-12-31"

    conn = get_connection()
    c = conn.cursor()

    solicitudes_creadas = []
    
    for (area, in_situ), grp_items in grupos.items():
        no_sol = solicitud_numbers.pop(0)
        
        c.execute("""
            INSERT INTO solicitudes_master (
                no_solicitud, no_folio, version, cliente, representante, telefono, correo, rfc, pais,
                es_extranjero, aplica_iva, fecha_recepcion, fecha_emision, vigencia, estado, es_in_situ, clave_area
            ) VALUES (?, ?, 1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'TURNADA', ?, ?)
        """, (
            no_sol, no_folio,
            cliente_data.get("cliente", ""),
            cliente_data.get("representante", ""),
            cliente_data.get("telefono", ""),
            cliente_data.get("correo", ""),
            cliente_data.get("rfc", ""),
            cliente_data.get("pais", "México"),
            1 if cliente_data.get("es_extranjero") else 0,
            0 if (cliente_data.get("es_extranjero") and cliente_data.get("aplica_iva")) else (1 if cliente_data.get("aplica_iva") else 0),
            now_str, hoy_str, vig_str, in_situ, area
        ))
        sol_master_id = c.lastrowid

        sla_limit = (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d")
        c.execute("""
            INSERT INTO sub_solicitudes_at (
                solicitud_id, clave_area, estado, fecha_asignacion, fecha_limite_sla
            ) VALUES (?, ?, 'ASIGNADA', ?, ?)
        """, (sol_master_id, area, now_str, sla_limit))
        sub_id = c.lastrowid

        for idx, eq in enumerate(grp_items, 1):
            c.execute("""
                INSERT INTO partidas (
                    sub_solicitud_id, solicitud_id, numero_partida, descripcion_equipo,
                    marca, modelo, no_serie, alcance_solicitado, descripcion_servicio,
                    certificado_anterior, magnitud, id_interno, condiciones_particulares,
                    es_in_situ
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                sub_id, sol_master_id, idx,
                eq.get("desc", eq.get("descripcion_equipo", "")),
                eq.get("marca", ""),
                eq.get("modelo", ""),
                eq.get("serie", eq.get("no_serie", "")),
                eq.get("alcance", eq.get("alcance_solicitado", "")),
                eq.get("desc_servicio", eq.get("descripcion_servicio", eq.get("desc", ""))),
                eq.get("cert", eq.get("certificado_anterior", "")),
                eq.get("mag", eq.get("magnitud", "")),
                eq.get("id", eq.get("id_interno", "")),
                eq.get("cond", eq.get("condiciones_particulares", "")),
                in_situ
            ))

        solicitudes_creadas.append({
            "solicitud_id": sol_master_id,
            "no_solicitud": no_sol,
            "clave_area": area,
            "es_in_situ": in_situ,
            "total_partidas": len(grp_items)
        })

    conn.commit()
    conn.close()

    return {
        "no_folio": no_folio,
        "solicitudes_creadas": solicitudes_creadas
    }

def separar_partidas_in_situ(solicitud_origen_id, partida_ids, user_correo="csat@cenam.mx"):
    """
    Separa una o más partidas de una solicitud ordinaria CENAM y genera una nueva solicitud IN SITU
    con viáticos, conservando exactamente el mismo No. de Folio para trazabilidad integral.
    """
    if not partida_ids:
        raise ValueError("Debe seleccionar al menos una partida para separar a la modalidad IN SITU.")

    conn = get_connection()
    c = conn.cursor()

    c.execute("SELECT * FROM solicitudes_master WHERE id = ?", (solicitud_origen_id,))
    orig = c.fetchone()
    if not orig:
        conn.close()
        raise ValueError(f"No se encontró la solicitud origen con ID {solicitud_origen_id}")

    orig_dict = dict(orig)
    no_folio = orig_dict["no_folio"]
    clave_area = orig_dict.get("clave_area") or "740"
    conn.close()

    nuevo_no_solicitud = get_next_solicitud_number()
    conn = get_connection()
    c = conn.cursor()

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    hoy_str = datetime.now().strftime("%Y-%m-%d")
    sla_limit = (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d")

    c.execute("""
        INSERT INTO solicitudes_master (
            no_solicitud, no_folio, version, cliente, representante, telefono, correo, rfc, pais,
            es_extranjero, aplica_iva, fecha_recepcion, fecha_emision, vigencia, estado, es_in_situ, clave_area
        ) VALUES (?, ?, 1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'TURNADA', 1, ?)
    """, (
        nuevo_no_solicitud, no_folio,
        orig_dict.get("cliente", ""),
        orig_dict.get("representante", ""),
        orig_dict.get("telefono", ""),
        orig_dict.get("correo", ""),
        orig_dict.get("rfc", ""),
        orig_dict.get("pais", "México"),
        orig_dict.get("es_extranjero", 0),
        orig_dict.get("aplica_iva", 1),
        now_str, hoy_str, orig_dict.get("vigencia", f"{datetime.now().year}-12-31"),
        clave_area
    ))
    nueva_sol_id = c.lastrowid

    c.execute("""
        INSERT INTO sub_solicitudes_at (
            solicitud_id, clave_area, estado, fecha_asignacion, fecha_limite_sla
        ) VALUES (?, ?, 'ASIGNADA', ?, ?)
    """, (nueva_sol_id, clave_area, now_str, sla_limit))
    nueva_sub_id = c.lastrowid

    for p_id in partida_ids:
        c.execute("""
            UPDATE partidas 
            SET solicitud_id = ?, sub_solicitud_id = ?, es_in_situ = 1 
            WHERE id = ?
        """, (nueva_sol_id, nueva_sub_id, p_id))

    conn.commit()
    conn.close()

    return {
        "nueva_solicitud_id": nueva_sol_id,
        "nuevo_no_solicitud": nuevo_no_solicitud,
        "no_folio": no_folio
    }

def get_expedientes_resumen():
    """Retorna la lista de expedientes agrupados por folio con sus solicitudes hijas."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT m.id, m.no_folio, m.no_solicitud, m.no_cotizacion, m.cliente, m.rfc,
               m.fecha_recepcion, m.fecha_emision, m.estado, m.es_in_situ, m.clave_area,
               a.nombre as nombre_area,
               COUNT(p.id) as total_partidas
        FROM solicitudes_master m
        LEFT JOIN areas_tecnicas a ON m.clave_area = a.clave
        LEFT JOIN partidas p ON m.id = p.solicitud_id
        GROUP BY m.id, m.no_folio, m.no_solicitud, m.no_cotizacion, m.cliente, m.rfc,
                 m.fecha_recepcion, m.fecha_emision, m.estado, m.es_in_situ, m.clave_area, a.nombre
        ORDER BY m.no_folio DESC, m.id ASC
    """)
    rows = c.fetchall()
    conn.close()

    from collections import OrderedDict
    expedientes = OrderedDict()
    for r in rows:
        d = dict(r)
        folio = d["no_folio"]
        if folio not in expedientes:
            expedientes[folio] = {
                "no_folio": folio,
                "cliente": d["cliente"],
                "rfc": d["rfc"],
                "fecha_recepcion": d["fecha_recepcion"],
                "solicitudes": []
            }
        expedientes[folio]["solicitudes"].append(d)

    return list(expedientes.values())

def get_laboratorios_por_area(clave_area):
    """Devuelve los laboratorios técnicos oficiales asociados a un Área Técnica."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT DISTINCT codigo, descripcion, id_division, id_area
        FROM laboratorios
        WHERE clave_area = ? AND es_laboratorio = 1 AND activo = 1
        ORDER BY codigo
    """, (clave_area,))
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def limpiar_solicitudes_y_programaciones():
    """
    Elimina todas las solicitudes, sub-solicitudes, partidas y consultas operativas,
    conservando intactos los catálogos de servicios, laboratorios y áreas técnicas.
    Reinicia las secuencias de SQLite para reiniciar folios desde 0001-2026PR.
    """
    conn = get_connection()
    c = conn.cursor()
    c.execute("PRAGMA foreign_keys = OFF;")
    
    conteos = {}
    for tbl in ["partidas", "sub_solicitudes_at", "consultas_especialistas", "solicitudes_master"]:
        try:
            c.execute(f"SELECT COUNT(*) FROM {tbl}")
            conteos[tbl] = c.fetchone()[0]
        except Exception:
            conteos[tbl] = 0
            
    c.execute("DELETE FROM partidas;")
    c.execute("DELETE FROM sub_solicitudes_at;")
    c.execute("DELETE FROM consultas_especialistas;")
    c.execute("DELETE FROM solicitudes_master;")
    
    try:
        c.execute("DELETE FROM sqlite_sequence WHERE name IN ('solicitudes_master', 'sub_solicitudes_at', 'partidas', 'consultas_especialistas');")
    except Exception:
        pass
        
    c.execute("PRAGMA foreign_keys = ON;")

    # 0. Usuarios y Autenticacion
    c.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id TEXT PRIMARY KEY,
        correo TEXT UNIQUE NOT NULL,
        nombre_completo TEXT NOT NULL,
        rol TEXT NOT NULL,
        clave_area TEXT,
        password_hash TEXT NOT NULL,
        activo INTEGER DEFAULT 1
    );
    """)

    conn.commit()
    conn.close()
    return conteos

# ========================================================
# FUNCIONES PARA PORTAL PÚBLICO Y ACCESO SEGURO CLIENTE (OTP)
# ========================================================

def hash_otp(codigo: str) -> str:
    salt = "cenam_otp_salt_2026"
    return hashlib.sha256((codigo.strip() + salt).encode("utf-8")).hexdigest()

def crear_codigo_otp(correo: str) -> str:
    """Genera y almacena un código OTP de 6 dígitos válido por 10 minutos."""
    correo_clean = correo.strip().lower()
    codigo = f"{random.randint(100000, 999999)}"
    h = hash_otp(codigo)
    now = datetime.now()
    exp = now + timedelta(minutes=10)
    now_str = now.strftime("%Y-%m-%d %H:%M:%S")
    exp_str = exp.strftime("%Y-%m-%d %H:%M:%S")

    conn = get_connection()
    c = conn.cursor()
    # Invalidar anteriores activos para este correo
    c.execute("UPDATE codigos_otp SET usado = 1 WHERE LOWER(correo) = ? AND usado = 0", (correo_clean,))
    # Registrar nuevo código
    c.execute("""
        INSERT INTO codigos_otp (correo, codigo_hash, expiracion, usado, creado_en)
        VALUES (?, ?, ?, 0, ?)
    """, (correo_clean, h, exp_str, now_str))
    conn.commit()
    conn.close()
    return codigo

def verificar_codigo_otp(correo: str, codigo: str) -> bool:
    """Valida el código OTP sin permitir reutilización."""
    correo_clean = correo.strip().lower()
    codigo_clean = codigo.strip().replace(" ", "").replace("-", "")
    h = hash_otp(codigo_clean)
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT id FROM codigos_otp
        WHERE LOWER(correo) = ? AND codigo_hash = ? AND usado = 0 AND expiracion >= ?
        ORDER BY id DESC LIMIT 1
    """, (correo_clean, h, now_str))
    row = c.fetchone()
    if row:
        otp_id = row['id']
        c.execute("UPDATE codigos_otp SET usado = 1 WHERE id = ?", (otp_id,))
        conn.commit()
        conn.close()
        return True
    conn.close()
    return False

def crear_solicitud_web(cliente_data: dict, instrumentos: list) -> dict:
    """Crea la solicitud desde el portal web asignándole Folio y Token de acceso directo."""
    token = uuid.uuid4().hex[:12].upper()
    resultado = crear_expediente_y_solicitudes(cliente_data, instrumentos, user_correo="portal.web@cenam.mx")
    no_folio = resultado["no_folio"]

    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE solicitudes_master SET token_seguimiento = ?, origen = 'WEB' WHERE no_folio = ?", (token, no_folio))
    conn.commit()
    conn.close()

    resultado["token_seguimiento"] = token
    return resultado

def consultar_solicitudes_cliente(correo: str = None, folio: str = None, token: str = None):
    """Consulta expedientes agrupados por folio para el panel del cliente."""
    conn = get_connection()
    c = conn.cursor()

    where_clauses = []
    params = []

    if correo and isinstance(correo, str) and correo.strip():
        where_clauses.append("LOWER(m.correo) = ?")
        params.append(correo.strip().lower())
    elif folio and token and isinstance(folio, str) and isinstance(token, str) and folio.strip() and token.strip():
        where_clauses.append("m.no_folio = ? AND (m.token_seguimiento = ? OR UPPER(m.token_seguimiento) = ?)")
        params.extend([folio.strip(), token.strip(), token.strip().upper()])
    elif folio and isinstance(folio, str) and folio.strip():
        where_clauses.append("m.no_folio = ?")
        params.append(folio.strip())
    else:
        conn.close()
        return []

    sql = f"""
        SELECT m.id, m.no_solicitud, m.no_folio, m.no_cotizacion, m.cliente, m.rfc, m.correo, m.telefono,
               m.fecha_recepcion, m.fecha_emision, m.vigencia, m.estado, m.es_in_situ, m.token_seguimiento,
               m.no_orden_compra, m.orden_compra_pdf, m.fecha_aceptacion_cliente, m.aplica_iva, m.clave_area,
               a.nombre as nombre_area
        FROM solicitudes_master m
        LEFT JOIN areas_tecnicas a ON m.clave_area = a.clave
        WHERE {' AND '.join(where_clauses)}
        ORDER BY m.id DESC
    """
    c.execute(sql, tuple(params))
    solicitudes = [dict(r) for r in c.fetchall()]

    folios_dict = {}
    for sol in solicitudes:
        fid = sol['no_folio']
        if fid not in folios_dict:
            folios_dict[fid] = {
                "no_folio": fid,
                "cliente": sol['cliente'],
                "rfc": sol['rfc'],
                "correo": sol['correo'],
                "telefono": sol['telefono'],
                "fecha_recepcion": sol['fecha_recepcion'],
                "estado_general": sol['estado'],
                "token_seguimiento": sol.get('token_seguimiento') or '',
                "no_orden_compra": sol.get('no_orden_compra') or '',
                "orden_compra_pdf": sol.get('orden_compra_pdf') or '',
                "fecha_aceptacion_cliente": sol.get('fecha_aceptacion_cliente') or '',
                "solicitudes": [],
                "partidas": [],
                "subtotal": 0.0,
                "iva": 0.0,
                "total": 0.0,
                "tiene_cotizacion": False
            }

        c.execute("""
            SELECT p.id, p.solicitud_id, p.sub_solicitud_id, p.numero_partida, p.descripcion_equipo,
                   p.marca, p.modelo, p.no_serie, p.alcance_solicitado, p.descripcion_servicio,
                   p.tiempo_dias_habiles, p.cantidad, p.precio_unitario, p.precio_total,
                   p.es_no_realizable, p.aceptada_cliente, p.estado_partida,
                   s.fecha_recepcion_prog, s.fecha_inicio_prog, s.fecha_entrega_prog
            FROM partidas p
            LEFT JOIN sub_solicitudes_at s ON p.sub_solicitud_id = s.id
            WHERE p.solicitud_id = ?
            ORDER BY p.numero_partida ASC
        """, (sol['id'],))
        partidas = [dict(p) for p in c.fetchall()]
        sol['partidas'] = partidas
        folios_dict[fid]['solicitudes'].append(sol)
        folios_dict[fid]['partidas'].extend(partidas)

        if sol.get('no_cotizacion'):
            folios_dict[fid]['tiene_cotizacion'] = True
            folios_dict[fid]['no_cotizacion'] = sol['no_cotizacion']
            folios_dict[fid]['fecha_emision_cot'] = sol['fecha_emision']
            folios_dict[fid]['vigencia_cot'] = sol['vigencia']

        for pt in partidas:
            if not pt.get('es_no_realizable'):
                pt_total = float(pt.get('precio_total') or 0.0)
                folios_dict[fid]['subtotal'] += pt_total

    for fid, f_data in folios_dict.items():
        sub = f_data['subtotal']
        iva = round(sub * 0.16, 2)
        f_data['iva'] = iva
        f_data['total'] = round(sub + iva, 2)

    conn.close()
    return list(folios_dict.values())

def aceptar_cotizacion_cliente(no_folio: str, datos_aceptacion: dict, token: str = None, correo: str = None):
    """Formaliza la aceptación de cotización por parte del cliente."""
    conn = get_connection()
    c = conn.cursor()

    if token:
        c.execute("SELECT id FROM solicitudes_master WHERE no_folio = ? AND (token_seguimiento = ? OR UPPER(token_seguimiento) = ?)", (no_folio, token, token.upper()))
    elif correo:
        c.execute("SELECT id FROM solicitudes_master WHERE no_folio = ? AND LOWER(correo) = ?", (no_folio, correo.strip().lower()))
    else:
        conn.close()
        raise ValueError("Credencial de acceso inválida para este folio.")

    rows = c.fetchall()
    if not rows:
        conn.close()
        raise ValueError("Folio no encontrado o no tiene permisos para aceptarlo.")

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    no_oc = datos_aceptacion.get("no_orden_compra", "").strip()
    pdf_path = datos_aceptacion.get("orden_compra_pdf", "")
    partidas_aceptadas = datos_aceptacion.get("partidas_aceptadas", [])

    c.execute("""
        UPDATE solicitudes_master
        SET estado = 'ACEPTADA_CLIENTE',
            no_orden_compra = ?,
            orden_compra_pdf = ?,
            fecha_aceptacion_cliente = ?,
            fecha_aceptacion_cotizacion = ?
        WHERE no_folio = ?
    """, (no_oc, pdf_path, now_str, now_str, no_folio))

    c.execute("""
        UPDATE sub_solicitudes_at
        SET estado = 'ACEPTADA'
        WHERE solicitud_id IN (SELECT id FROM solicitudes_master WHERE no_folio = ?)
    """, (no_folio,))

    if partidas_aceptadas:
        for pid in partidas_aceptadas:
            c.execute("UPDATE partidas SET aceptada_cliente = 1 WHERE id = ?", (pid,))

    conn.commit()
    conn.close()

    log_auditoria(correo or "cliente.portal@cenam.mx", "ACEPTACION_COTIZACION_CLIENTE", "SOLICITUD_MASTER", no_folio, {
        "no_orden_compra": no_oc,
        "partidas_aceptadas": partidas_aceptadas,
        "fecha": now_str
    })

    return {"status": "success", "no_folio": no_folio, "mensaje": "Aceptación registrada con éxito."}

if __name__ == "__main__":
    init_db()
    print("Base de datos local inicializada y actualizada con éxito.")
    print("Siguiente Solicitud:", get_next_solicitud_number())
    print("Siguiente Folio:", get_next_folio_number())
    print("Siguiente Cotización:", get_next_cotizacion_number())
