import sqlite3
import os
import sys

sys.path.insert(0, os.path.abspath("nube_segura"))
import cloud_db as cdb

def sync():
    print("Conectando a Supabase PostgreSQL...")
    conn, engine = cdb.get_db_connection()
    if engine != "POSTGRES":
        print("ERROR: No se conectó a PostgreSQL. Motor actual:", engine)
        return
    
    print("Conexión a PostgreSQL confirmada.")
    sqlite_conn = sqlite3.connect("nube_segura/cloud_cenam_secure.db")
    sqlite_conn.row_factory = sqlite3.Row
    s_cur = sqlite_conn.cursor()
    
    pg_cur = conn.conn.cursor()
    
    # 1. Áreas Técnicas
    pg_cur.execute("SELECT COUNT(*) FROM areas_tecnicas")
    cnt_areas = pg_cur.fetchone()[0]
    if cnt_areas == 0:
        s_cur.execute("SELECT clave, nombre FROM areas_tecnicas")
        areas = s_cur.fetchall()
        for a in areas:
            pg_cur.execute("INSERT INTO areas_tecnicas (clave, nombre) VALUES (%s, %s) ON CONFLICT (clave) DO NOTHING", (a['clave'], a['nombre']))
        conn.commit()
        print(f"-> {len(areas)} Áreas Técnicas sincronizadas en Supabase.")
    else:
        print(f"-> Áreas Técnicas ya existen en Supabase ({cnt_areas} registros).")
        
    # 2. Usuarios
    pg_cur.execute("SELECT COUNT(*) FROM usuarios")
    cnt_usr = pg_cur.fetchone()[0]
    if cnt_usr == 0:
        s_cur.execute("SELECT correo, nombre_completo, rol, clave_area, password_hash, activo FROM usuarios")
        users = s_cur.fetchall()
        for u in users:
            pg_cur.execute("""
            INSERT INTO usuarios (correo, nombre_completo, rol, clave_area, password_hash, activo)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (correo) DO NOTHING
            """, (u['correo'], u['nombre_completo'], u['rol'], u['clave_area'], u['password_hash'], bool(u['activo'])))
        conn.commit()
        print(f"-> {len(users)} Usuarios RBAC sincronizados en Supabase.")
    else:
        print(f"-> Usuarios ya existen en Supabase ({cnt_usr} registros).")

    # 3. Catálogo de Servicios
    pg_cur.execute("SELECT COUNT(*) FROM catalogo_servicios")
    cnt_cat = pg_cur.fetchone()[0]
    if cnt_cat == 0:
        s_cur.execute("""
        SELECT clave_servicio, clave_area, nombre_tramite, supuesto, alcance, observaciones,
               costo, fundamento_juridico, es_in_situ, dias_habiles_defecto
        FROM catalogo_servicios
        """)
        services = s_cur.fetchall()
        for s in services:
            pg_cur.execute("""
            INSERT INTO catalogo_servicios (
                clave_servicio, clave_area, nombre_tramite, supuesto, alcance, observaciones,
                costo, fundamento_juridico, es_in_situ, dias_habiles_defecto
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                s['clave_servicio'], s['clave_area'], s['nombre_tramite'], s['supuesto'],
                s['alcance'], s['observaciones'], float(s['costo'] or 0), s['fundamento_juridico'],
                s['es_in_situ'], int(s['dias_habiles_defecto'] or 5)
            ))
        conn.commit()
        print(f"-> {len(services)} Servicios del Catálogo Oficial sincronizados en Supabase.")
    else:
        print(f"-> Catálogo ya existe en Supabase ({cnt_cat} registros).")
        
    sqlite_conn.close()
    conn.close()
    print("Sincronización inicial con Supabase finalizada con ÉXITO.")

if __name__ == '__main__':
    sync()
