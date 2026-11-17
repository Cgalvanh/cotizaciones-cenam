import os
import sys
import sqlite3
import pandas as pd

# Path setup
sys.path.insert(0, os.path.abspath("nube_segura"))
sys.path.insert(0, os.path.abspath("."))
import cloud_db as cdb
import database as local_db

def sync_all():
    print("="*70)
    print("SINCRONIZANDO CATALOGO OFICIAL (612 SERVICIOS) Y 294 LABORATORIOS")
    print("="*70)

    # 1. Cargar DataFrames
    df_serv = pd.read_csv("data/catalogo_servicios_completo_cenam.csv")
    df_labs = pd.read_csv("data/laboratorios_cenam_completo.csv")
    print(f"Cargados desde CSV: {len(df_serv)} servicios y {len(df_labs)} laboratorios.")

    DIV_TO_AT = {
        740: 'AT-01', 410: 'AT-02', 440: 'AT-03', 430: 'AT-04',
        420: 'AT-05', 520: 'AT-06', 730: 'AT-07', 720: 'AT-08',
        710: 'AT-09', 510: 'AT-10', 610: 'AT-11', 700: 'AT-11',
        620: 'AT-12', 630: 'AT-13', 800: 'AT-14', 810: 'AT-14'
    }

    # -------------------------------------------------------------------------
    # A. SINCRONIZAR BASE DE DATOS LOCAL (SQLite)
    # -------------------------------------------------------------------------
    print("\n--- 1. Sincronizando Base de Datos Local (SQLite) ---")
    local_db.init_db()
    l_conn = local_db.get_connection()
    l_cur = l_conn.cursor()

    # Crear tabla laboratorios si no existe
    l_cur.execute("""
    CREATE TABLE IF NOT EXISTS laboratorios (
        id_uni INTEGER PRIMARY KEY,
        codigo TEXT NOT NULL,
        descripcion TEXT NOT NULL,
        id_division INTEGER,
        id_area INTEGER,
        activo INTEGER DEFAULT 1,
        es_laboratorio INTEGER DEFAULT 1,
        clave_area TEXT
    );
    """)

    # Asegurar columnas nuevas en catalogo_servicios
    l_cols = [c[1] for c in l_cur.execute("PRAGMA table_info(catalogo_servicios)").fetchall()]
    for col_name, col_type in [
        ('codigo_laboratorio', 'TEXT'),
        ('nombre_laboratorio', 'TEXT'),
        ('codigo_division', 'INTEGER'),
        ('metodo', 'TEXT'),
        ('incertidumbre', 'TEXT')
    ]:
        if col_name not in l_cols:
            l_cur.execute(f"ALTER TABLE catalogo_servicios ADD COLUMN {col_name} {col_type};")

    # Insertar/Actualizar laboratorios
    l_cur.execute("DELETE FROM laboratorios;")
    for _, r in df_labs.iterrows():
        div_id = int(r['id_division']) if pd.notnull(r['id_division']) else None
        clave_at = DIV_TO_AT.get(div_id, 'AT-01')
        l_cur.execute("""
        INSERT INTO laboratorios (id_uni, codigo, descripcion, id_division, id_area, activo, es_laboratorio, clave_area)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            int(r['id_uni']), str(r['codigo']), str(r['descripcion'] or ''),
            div_id, int(r['id_area']) if pd.notnull(r['id_area']) else None,
            1 if r['activo'] else 0, 1 if r['laboratorio'] else 0, clave_at
        ))

    # Insertar/Actualizar servicios
    for _, s in df_serv.iterrows():
        l_cur.execute("""
        INSERT INTO catalogo_servicios (
            clave_servicio, clave_area, nombre_tramite, supuesto, alcance, observaciones,
            costo, fundamento_juridico, es_in_situ, dias_habiles_defecto,
            codigo_laboratorio, nombre_laboratorio, codigo_division, metodo, incertidumbre
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(clave_servicio) DO UPDATE SET
            clave_area=excluded.clave_area,
            nombre_tramite=excluded.nombre_tramite,
            supuesto=excluded.supuesto,
            alcance=excluded.alcance,
            observaciones=excluded.observaciones,
            costo=excluded.costo,
            dias_habiles_defecto=excluded.dias_habiles_defecto,
            codigo_laboratorio=excluded.codigo_laboratorio,
            nombre_laboratorio=excluded.nombre_laboratorio,
            codigo_division=excluded.codigo_division,
            metodo=excluded.metodo,
            incertidumbre=excluded.incertidumbre
        """, (
            s['clave_servicio'], s['clave_area'], f"Calibración {s['codigo_laboratorio']}",
            s['descripcion'], str(s['intervalo'] or ''), str(s['observaciones'] or ''),
            float(s['precio']), "Art. 58 Fracc. III Ley Federal de Entidades Paraestatales",
            'NO', int(s['tiempo_dias_habiles']),
            s['codigo_laboratorio'], s['nombre_laboratorio'], int(s['codigo_division']),
            str(s['metodo'] or ''), str(s['incertidumbre'] or '')
        ))

    l_conn.commit()
    cnt_l_labs = l_cur.execute("SELECT COUNT(*) FROM laboratorios").fetchone()[0]
    cnt_l_serv = l_cur.execute("SELECT COUNT(*) FROM catalogo_servicios").fetchone()[0]
    l_conn.close()
    print(f"  -> SQLite: {cnt_l_labs} Laboratorios y {cnt_l_serv} Servicios en catálogo.")

    # -------------------------------------------------------------------------
    # B. SINCRONIZAR BASE DE DATOS EN LA NUBE (Supabase PostgreSQL)
    # -------------------------------------------------------------------------
    print("\n--- 2. Sincronizando Base de Datos en Supabase PostgreSQL ---")
    conn, engine = cdb.get_db_connection()
    if engine != "POSTGRES":
        print("Aviso: Conectado a SQLite de respaldo, no se pudo conectar a Supabase.")
        return

    c = conn.cursor()
    # Crear tabla laboratorios en Supabase
    c.execute("""
    CREATE TABLE IF NOT EXISTS laboratorios (
        id_uni INTEGER PRIMARY KEY,
        codigo TEXT NOT NULL,
        descripcion TEXT NOT NULL,
        id_division INTEGER,
        id_area INTEGER,
        activo INTEGER DEFAULT 1,
        es_laboratorio INTEGER DEFAULT 1,
        clave_area TEXT
    );
    """)

    # Agregar columnas si no existen en catalogo_servicios de PostgreSQL
    for col_def in [
        "ADD COLUMN IF NOT EXISTS codigo_laboratorio TEXT",
        "ADD COLUMN IF NOT EXISTS nombre_laboratorio TEXT",
        "ADD COLUMN IF NOT EXISTS codigo_division INTEGER",
        "ADD COLUMN IF NOT EXISTS metodo TEXT",
        "ADD COLUMN IF NOT EXISTS incertidumbre TEXT"
    ]:
        c.execute(f"ALTER TABLE catalogo_servicios {col_def};")

    conn.commit()

    # Sincronizar laboratorios en PostgreSQL
    c.execute("DELETE FROM laboratorios;")
    for _, r in df_labs.iterrows():
        div_id = int(r['id_division']) if pd.notnull(r['id_division']) else None
        clave_at = DIV_TO_AT.get(div_id, 'AT-01')
        c.execute("""
        INSERT INTO laboratorios (id_uni, codigo, descripcion, id_division, id_area, activo, es_laboratorio, clave_area)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            int(r['id_uni']), str(r['codigo']), str(r['descripcion'] or ''),
            div_id, int(r['id_area']) if pd.notnull(r['id_area']) else None,
            1 if r['activo'] else 0, 1 if r['laboratorio'] else 0, clave_at
        ))

    # Sincronizar servicios en PostgreSQL
    for _, s in df_serv.iterrows():
        c.execute("""
        INSERT INTO catalogo_servicios (
            clave_servicio, clave_area, nombre_tramite, supuesto, alcance, observaciones,
            costo, fundamento_juridico, es_in_situ, dias_habiles_defecto,
            codigo_laboratorio, nombre_laboratorio, codigo_division, metodo, incertidumbre
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(clave_servicio) DO UPDATE SET
            clave_area=excluded.clave_area,
            nombre_tramite=excluded.nombre_tramite,
            supuesto=excluded.supuesto,
            alcance=excluded.alcance,
            observaciones=excluded.observaciones,
            costo=excluded.costo,
            dias_habiles_defecto=excluded.dias_habiles_defecto,
            codigo_laboratorio=excluded.codigo_laboratorio,
            nombre_laboratorio=excluded.nombre_laboratorio,
            codigo_division=excluded.codigo_division,
            metodo=excluded.metodo,
            incertidumbre=excluded.incertidumbre
        """, (
            s['clave_servicio'], s['clave_area'], f"Calibración {s['codigo_laboratorio']}",
            s['descripcion'], str(s['intervalo'] or ''), str(s['observaciones'] or ''),
            float(s['precio']), "Art. 58 Fracc. III Ley Federal de Entidades Paraestatales",
            'NO', int(s['tiempo_dias_habiles']),
            s['codigo_laboratorio'], s['nombre_laboratorio'], int(s['codigo_division']),
            str(s['metodo'] or ''), str(s['incertidumbre'] or '')
        ))

    conn.commit()
    c.execute("SELECT COUNT(*) FROM laboratorios;")
    cnt_pg_labs = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM catalogo_servicios;")
    cnt_pg_serv = c.fetchone()[0]
    conn.close()

    print(f"  -> Supabase: {cnt_pg_labs} Laboratorios y {cnt_pg_serv} Servicios en catálogo.")
    print("\n" + "="*70)
    print("SINCRONIZACIÓN EXITOSA EN AMBAS BASES DE DATOS.")
    print("="*70)

if __name__ == "__main__":
    sync_all()
