import sys
import os

sys.path.insert(0, os.path.abspath("nube_segura"))
import cloud_db as cdb

cdb.init_cloud_db()
conn, engine = cdb.get_db_connection()
c = conn.cursor()
c.execute("SELECT clave, nombre FROM areas_tecnicas ORDER BY clave LIMIT 3")
rows = c.fetchall()
print("Areas test:", [dict(r) for r in rows])

u = cdb.verify_credentials("ssi@cenam.mx", "Cenam2026*")
print("User verify test:", u["correo"], u["rol"])
conn.close()
