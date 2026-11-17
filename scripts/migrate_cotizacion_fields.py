#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de migración para ambas bases (SQLite Local y Supabase PostgreSQL):
- Agregar comentarios_ssi a partidas
- Agregar comentarios_cliente a partidas
- Agregar estado_partida a partidas (COTIZADA, ACEPTADA, DECLINADA_POR_CLIENTE)
- Agregar orden_compra_cliente a solicitudes_master
"""

import os
import sys
import sqlite3

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.join(PROJECT_ROOT, "nube_segura"))

def migrar_sqlite():
    db_path = os.path.join(PROJECT_ROOT, "cotizaciones_cenam.db")
    if not os.path.exists(db_path):
        print(f"[SQLite] Archivo {db_path} no existe.")
        return
        
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    
    cur.execute("PRAGMA table_info(partidas)")
    cols_p = [r[1] for r in cur.fetchall()]
    
    if "comentarios_ssi" not in cols_p:
        cur.execute("ALTER TABLE partidas ADD COLUMN comentarios_ssi TEXT;")
        print("[SQLite] Agregada columna comentarios_ssi a partidas")
    else:
        print("[SQLite] comentarios_ssi ya existe en partidas")

    if "comentarios_cliente" not in cols_p:
        cur.execute("ALTER TABLE partidas ADD COLUMN comentarios_cliente TEXT;")
        print("[SQLite] Agregada columna comentarios_cliente a partidas")
    else:
        print("[SQLite] comentarios_cliente ya existe en partidas")

    if "estado_partida" not in cols_p:
        cur.execute("ALTER TABLE partidas ADD COLUMN estado_partida TEXT DEFAULT 'COTIZADA';")
        print("[SQLite] Agregada columna estado_partida a partidas")
    else:
        print("[SQLite] estado_partida ya existe en partidas")

    cur.execute("PRAGMA table_info(solicitudes_master)")
    cols_m = [r[1] for r in cur.fetchall()]
    
    if "orden_compra_cliente" not in cols_m:
        cur.execute("ALTER TABLE solicitudes_master ADD COLUMN orden_compra_cliente TEXT;")
        print("[SQLite] Agregada columna orden_compra_cliente a solicitudes_master")
    else:
        print("[SQLite] orden_compra_cliente ya existe en solicitudes_master")

    con.commit()
    con.close()
    print("[SQLite] Migracion local completada exitosamente.")

def migrar_postgres():
    import cloud_db as cdb
    conn, engine = cdb.get_db_connection()
    if engine != "POSTGRES":
        print("[PostgreSQL] No esta conectado en modo POSTGRES.")
        conn.close()
        return

    c = conn.cursor()
    print("[PostgreSQL] Conectado a Supabase PostgreSQL. Ejecutando migracion...")
    
    queries = [
        "ALTER TABLE partidas ADD COLUMN IF NOT EXISTS comentarios_ssi TEXT;",
        "ALTER TABLE partidas ADD COLUMN IF NOT EXISTS comentarios_cliente TEXT;",
        "ALTER TABLE partidas ADD COLUMN IF NOT EXISTS estado_partida VARCHAR(50) DEFAULT 'COTIZADA';",
        "ALTER TABLE solicitudes_master ADD COLUMN IF NOT EXISTS orden_compra_cliente VARCHAR(150);"
    ]
    
    for q in queries:
        try:
            c.execute(q)
            print(f"  [OK] {q}")
        except Exception as e:
            print(f"  [AVISO] {e}")

    conn.commit()
    conn.close()
    print("[PostgreSQL] Migracion en Supabase completada exitosamente.")

if __name__ == "__main__":
    print("="*60)
    print("MIGRACION DE CAMPOS DE COTIZACION Y ACEPTACION EN AMBAS BASES")
    print("="*60)
    migrar_sqlite()
    print("-" * 60)
    migrar_postgres()
    print("="*60)
    print("MIGRACION FINALIZADA")
    print("="*60)
