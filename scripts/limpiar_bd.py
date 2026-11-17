#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
HERRAMIENTA OFICIAL DE LIMPIEZA DE BASE DE DATOS OPERATIVA (CENAM)
=============================================================================
Este script permite depurar todas las solicitudes, sub-solicitudes, partidas,
programaciones de laboratorio y consultas de prueba, permitiendo reiniciar el
sistema con un estado operativo limpio (Folio 0001-2026PR y Solicitud 2026001PR).

PROTECCION ESTRICTA DE CATALOGOS:
- catalogo_servicios (1,036 servicios)   -> CONSERVADO
- laboratorios (294 laboratorios)        -> CONSERVADO
- areas_tecnicas (15 direcciones)        -> CONSERVADO
- usuarios (credenciales y accesos)      -> CONSERVADO
=============================================================================
"""

import os
import sys
import argparse
import sqlite3

# Asegurar importación de módulos del proyecto
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.join(PROJECT_ROOT, "nube_segura"))

from dotenv import load_dotenv
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

TABLAS_OPERATIVAS = [
    "partidas",
    "sub_solicitudes_at",
    "consultas_especialistas",
    "solicitudes_master"
]

TABLAS_CATALOGOS = [
    "catalogo_servicios",
    "laboratorios",
    "areas_tecnicas",
    "usuarios"
]

def obtener_conteos_sqlite(db_path):
    if not os.path.exists(db_path):
        return None
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    conteos = {}
    
    # Operativas
    for t in TABLAS_OPERATIVAS:
        try:
            c.execute(f"SELECT COUNT(*) FROM {t}")
            conteos[t] = c.fetchone()[0]
        except Exception:
            conteos[t] = 0
            
    # Catálogos
    for t in ["catalogo_servicios", "laboratorios", "areas_tecnicas"]:
        try:
            c.execute(f"SELECT COUNT(*) FROM {t}")
            conteos[t] = c.fetchone()[0]
        except Exception:
            conteos[t] = 0
            
    conn.close()
    return conteos

def obtener_conteos_postgres():
    try:
        import cloud_db as cdb
        conn, engine = cdb.get_db_connection()
        if engine != "POSTGRES":
            conn.close()
            return None
        c = conn.cursor()
        conteos = {}
        for t in TABLAS_OPERATIVAS + ["bitacora_auditoria"] + TABLAS_CATALOGOS:
            try:
                c.execute(f"SELECT COUNT(*) as cnt FROM {t}")
                row = c.fetchone()
                conteos[t] = row["cnt"] if isinstance(row, dict) else row[0]
            except Exception:
                conteos[t] = 0
        conn.close()
        return conteos
    except Exception as e:
        print(f"  [ERROR] No se pudo conectar a PostgreSQL Supabase: {e}")
        return None

def limpiar_sqlite(db_path, limpiar_todo=False):
    if not os.path.exists(db_path):
        print(f"  [AVISO] Archivo SQLite no encontrado en: {db_path}")
        return {}

    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("PRAGMA foreign_keys = OFF;")
    
    eliminados = {}
    for t in TABLAS_OPERATIVAS:
        try:
            c.execute(f"SELECT COUNT(*) FROM {t}")
            cnt = c.fetchone()[0]
            c.execute(f"DELETE FROM {t};")
            eliminados[t] = cnt
        except Exception as e:
            eliminados[t] = f"Error: {e}"

    if limpiar_todo:
        for t in ["catalogo_servicios", "laboratorios", "areas_tecnicas"]:
            try:
                c.execute(f"DELETE FROM {t};")
            except Exception:
                pass
        print("  [ADVERTENCIA] Catálogos locales eliminados (--todo activo).")
    else:
        # Reset secuencias
        try:
            c.execute("DELETE FROM sqlite_sequence WHERE name IN ('solicitudes_master', 'sub_solicitudes_at', 'partidas', 'consultas_especialistas');")
        except Exception:
            pass

    c.execute("PRAGMA foreign_keys = ON;")
    conn.commit()
    conn.close()
    return eliminados

def limpiar_postgres(limpiar_auditoria=True, limpiar_todo=False):
    import cloud_db as cdb
    conn, engine = cdb.get_db_connection()
    c = conn.cursor()
    
    eliminados = {}
    for t in TABLAS_OPERATIVAS:
        try:
            c.execute(f"SELECT COUNT(*) as cnt FROM {t}")
            row = c.fetchone()
            cnt = row["cnt"] if isinstance(row, dict) else row[0]
            c.execute(f"DELETE FROM {t};")
            eliminados[t] = cnt
        except Exception as e:
            eliminados[t] = f"Error: {e}"

    if limpiar_auditoria:
        try:
            c.execute("SELECT COUNT(*) as cnt FROM bitacora_auditoria")
            row = c.fetchone()
            cnt = row["cnt"] if isinstance(row, dict) else row[0]
            c.execute("DELETE FROM bitacora_auditoria;")
            eliminados["bitacora_auditoria"] = cnt
        except Exception:
            pass

    if limpiar_todo:
        for t in TABLAS_CATALOGOS:
            try:
                c.execute(f"DELETE FROM {t};")
            except Exception:
                pass
        print("  [ADVERTENCIA] Catálogos y usuarios en la nube eliminados (--todo activo).")
    else:
        # Reiniciar secuencias de IDs
        secuencias = [
            "solicitudes_master_id_seq",
            "sub_solicitudes_at_id_seq",
            "partidas_id_seq",
            "consultas_especialistas_id_seq",
            "bitacora_auditoria_id_seq"
        ]
        for seq in secuencias:
            try:
                c.execute(f"ALTER SEQUENCE IF EXISTS {seq} RESTART WITH 1;")
            except Exception:
                pass

    conn.commit()
    conn.close()
    return eliminados

def limpiar_documentos_pdf():
    gen_dir = os.path.join(PROJECT_ROOT, "generated_docs")
    if not os.path.exists(gen_dir):
        return 0
    count = 0
    for root, dirs, files in os.walk(gen_dir):
        for f in files:
            if f.lower().endswith(".pdf"):
                try:
                    os.remove(os.path.join(root, f))
                    count += 1
                except Exception:
                    pass
    return count

def main():
    parser = argparse.ArgumentParser(
        description="Procedimiento para depurar solicitudes, partidas y programaciones en CENAM."
    )
    parser.add_argument(
        "--modo",
        choices=["local", "cloud", "ambas"],
        default="ambas",
        help="Base de datos a limpiar: 'local' (SQLite), 'cloud' (Supabase), o 'ambas' (defecto)."
    )
    parser.add_argument(
        "--yes", "-y",
        action="store_true",
        help="Ejecutar directamente sin solicitar confirmación interactiva."
    )
    parser.add_argument(
        "--conservar-auditoria",
        action="store_true",
        help="Conserva los registros de bitacora_auditoria (por defecto se depuran las pruebas)."
    )
    parser.add_argument(
        "--limpiar-pdfs",
        action="store_true",
        default=True,
        help="Elimina también los archivos PDF de prueba generados en generated_docs/ (defecto: True)."
    )
    parser.add_argument(
        "--no-pdfs",
        action="store_true",
        help="No elimina los PDFs generados."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Muestra el estado y registros actuales sin modificar la base de datos."
    )
    parser.add_argument(
        "--todo",
        action="store_true",
        help="[PELIGRO] Elimina también catálogos y usuarios (uso exclusivo para reinstalación total)."
    )
    args = parser.parse_args()

    db_local_path = os.path.join(PROJECT_ROOT, "cotizaciones_cenam.db")

    print("\n" + "="*75)
    print(" [CENAM]  CENTRO NACIONAL DE METROLOGIA - PROCEDIMIENTO DE LIMPIEZA OPERATIVA")
    print("="*75)
    print(f"Modo seleccionado: {args.modo.upper()}")
    print(f"Conserva Catálogos (Servicios, Labs, Areas): {'NO (--todo)' if args.todo else 'SI (100% Protegidos)'}")
    print(f"Conserva Usuarios: {'NO (--todo)' if args.todo else 'SI (100% Protegidos)'}")

    # 1. Diagnóstico previo
    print("\n--- [1] ESTADO ACTUAL DE REGISTROS ---")
    if args.modo in ["local", "ambas"]:
        cnt_sq = obtener_conteos_sqlite(db_local_path)
        if cnt_sq:
            print(f"[LOCAL] SQLite Local ({os.path.basename(db_local_path)}):")
            for t in TABLAS_OPERATIVAS:
                print(f"   * {t:<26}: {cnt_sq.get(t, 0)} registro(s)")
            print(f"   [Catálogos protegidos: servicios={cnt_sq.get('catalogo_servicios', 0)}, labs={cnt_sq.get('laboratorios', 0)}, areas={cnt_sq.get('areas_tecnicas', 0)}]")
        else:
            print("   * SQLite Local: No encontrado.")

    if args.modo in ["cloud", "ambas"]:
        cnt_pg = obtener_conteos_postgres()
        if cnt_pg:
            print(f"[CLOUD]  Supabase PostgreSQL (Nube Centralizada):")
            for t in TABLAS_OPERATIVAS + ["bitacora_auditoria"]:
                print(f"   * {t:<26}: {cnt_pg.get(t, 0)} registro(s)")
            print(f"   [Catálogos protegidos: servicios={cnt_pg.get('catalogo_servicios', 0)}, labs={cnt_pg.get('laboratorios', 0)}, areas={cnt_pg.get('areas_tecnicas', 0)}, usuarios={cnt_pg.get('usuarios', 0)}]")
        else:
            print("   * Supabase PostgreSQL: Sin conexión o inactivo.")

    if args.dry_run:
        print("\n[DRY-RUN] Modo simulación activo. No se realizó ninguna eliminación.")
        print("="*75)
        return

    # 2. Confirmación
    if not args.yes:
        print("\n" + "!"*75)
        print(" ATENCION: Se eliminarán todas las solicitudes, partidas y programaciones.")
        if args.todo:
            print(" ADVERTENCIA MAXIMA: Ha indicado --todo, lo que también borrará los catálogos.")
        print("!"*75)
        try:
            resp = input("¿Desea proceder con la limpieza operativa? (escriba 'si' o 's' para confirmar): ").strip().lower()
        except KeyboardInterrupt:
            print("\nOperación cancelada por el usuario.")
            return
            
        if resp not in ["si", "s", "yes", "y"]:
            print("Operación cancelada. No se modificó la base de datos.")
            return

    # 3. Ejecución de la limpieza
    print("\n--- [2] EJECUTANDO LIMPIEZA OPERATIVA ---")
    if args.modo in ["local", "ambas"]:
        print("[LIMPIANDO] Limpiando SQLite local...")
        res_sq = limpiar_sqlite(db_local_path, limpiar_todo=args.todo)
        for k, v in res_sq.items():
            print(f"   [OK] {k}: {v} eliminados.")

    if args.modo in ["cloud", "ambas"]:
        print("[LIMPIANDO] Limpiando Supabase PostgreSQL...")
        res_pg = limpiar_postgres(
            limpiar_auditoria=not args.conservar_auditoria,
            limpiar_todo=args.todo
        )
        for k, v in res_pg.items():
            print(f"   [OK] {k}: {v} eliminados.")

    if not args.no_pdfs and args.limpiar_pdfs:
        n_pdfs = limpiar_documentos_pdf()
        print(f"[PDF] Eliminados {n_pdfs} archivos PDF de prueba en 'generated_docs/'.")

    # 4. Estado de los siguientes folios
    print("\n--- [3] PROXIMOS FOLIOS DISPONIBLES TRAS LA LIMPIEZA ---")
    try:
        if args.modo in ["local", "ambas"]:
            import database as db
            print(f"   * Siguiente Solicitud SQLite: {db.get_next_solicitud_number()}")
            print(f"   * Siguiente Folio SQLite    : {db.get_next_folio_number()}")
            print(f"   * Siguiente Cotización SQLite: {db.get_next_cotizacion_number()}")
        if args.modo in ["cloud", "ambas"]:
            import cloud_db as cdb
            print(f"   * Siguiente Solicitud Cloud : {cdb.get_next_solicitud_numbers(1)[0]}")
            print(f"   * Siguiente Folio Cloud     : {cdb.get_next_folio_number()}")
            print(f"   * Siguiente Cotización Cloud: {cdb.get_next_cotizacion_number()}")
    except Exception as e:
        print(f"   [AVISO] No se pudo consultar el generador de folios: {e}")

    print("\n" + "="*75)
    print(" [OK] LIMPIEZA OPERATIVA FINALIZADA CON EXITO")
    print(" El sistema está listo para registrar nuevas solicitudes desde cero.")
    print("="*75 + "\n")

if __name__ == "__main__":
    main()
