import sys, os
sys.path.insert(0, os.path.abspath("nube_segura"))
import cloud_db as cdb

conn, engine = cdb.get_db_connection()
c = conn.conn.cursor()
c.execute("""
SELECT table_name, column_name, data_type 
FROM information_schema.columns 
WHERE table_schema = %s AND table_name IN (%s, %s, %s)
ORDER BY table_name, ordinal_position
""", ("public", "solicitudes_master", "partidas", "usuarios"))
for r in c.fetchall():
    print(f"{r[0]}.{r[1]}: {r[2]}")
conn.close()
