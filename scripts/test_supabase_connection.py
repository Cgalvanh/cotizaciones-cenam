import os
import sys

# Agregar nube_segura al path
sys.path.insert(0, os.path.abspath("nube_segura"))
sys.path.insert(0, os.path.abspath("."))

import cloud_db as cdb

def main():
    print("========================================================")
    print("  Diagnóstico de Conexión a Base de Datos Supabase")
    print("========================================================")
    
    url = cdb.get_database_url()
    print(f"DATABASE_URL detectada:\n  {url}\n")
    
    if "YOUR-PASSWORD" in url:
        print("[!] ATENCION: La URL todavía contiene el marcador YOUR-PASSWORD.")
        print("    Por favor proporcione su contraseña o actualícela en el archivo .env")
        if len(sys.argv) > 1:
            pwd = sys.argv[1]
            print(f"    Intentando con la contraseña proporcionada por argumento...")
            test_url = f"postgresql://postgres:{pwd}@db.lmvpzqniqjhdtjmmxvdg.supabase.co:5432/postgres?sslmode=require"
            ok, msg, m_type = cdb.test_postgres_connection(test_url)
            print(f"    Resultado: {'OK' if ok else 'FALLO'}")
            print(f"    Detalle: {msg}")
            if ok:
                cdb.update_supabase_password(pwd)
                print(f"    Contraseña guardada en .env exitosamente.")
                cdb.init_cloud_db()
                print(f"    Base de datos inicializada en Supabase.")
        else:
            print("    Uso: python scripts/test_supabase_connection.py <TU_CONTRASEÑA>")
        return

    print("Probando conexión a PostgreSQL...")
    ok, msg, m_type = cdb.test_postgres_connection(url)
    print(f"Resultado: {'OK' if ok else 'FALLO'}")
    print(f"Modo: {m_type}")
    print(f"Detalle: {msg}\n")
    
    if ok:
        print("Inicializando / verificando esquema en Supabase...")
        cdb.init_cloud_db()
        conn, engine = cdb.get_db_connection()
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM areas_tecnicas")
        n_areas = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM catalogo_servicios")
        n_cat = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM usuarios")
        n_usr = c.fetchone()[0]
        conn.close()
        print(f"Verificación exitosa en Supabase:")
        print(f"  • Áreas Técnicas: {n_areas}")
        print(f"  • Servicios en Catálogo: {n_cat}")
        print(f"  • Usuarios RBAC configurados: {n_usr}")
        print("\n¡Todo listo para correr en local con Supabase!")

if __name__ == "__main__":
    main()
