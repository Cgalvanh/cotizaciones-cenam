import sys, os
sys.path.insert(0, os.path.abspath("nube_segura"))
import cloud_db as cdb

conn, engine = cdb.get_db_connection()
c = conn.conn.cursor()

sqls = [
    # solicitudes_master
    "ALTER TABLE solicitudes_master ALTER COLUMN es_extranjero DROP DEFAULT;",
    "ALTER TABLE solicitudes_master ALTER COLUMN es_extranjero TYPE INTEGER USING (CASE WHEN es_extranjero THEN 1 ELSE 0 END);",
    "ALTER TABLE solicitudes_master ALTER COLUMN es_extranjero SET DEFAULT 0;",
    
    "ALTER TABLE solicitudes_master ALTER COLUMN aplica_iva DROP DEFAULT;",
    "ALTER TABLE solicitudes_master ALTER COLUMN aplica_iva TYPE INTEGER USING (CASE WHEN aplica_iva THEN 1 ELSE 0 END);",
    "ALTER TABLE solicitudes_master ALTER COLUMN aplica_iva SET DEFAULT 1;",
    
    "ALTER TABLE solicitudes_master ALTER COLUMN es_in_situ DROP DEFAULT;",
    "ALTER TABLE solicitudes_master ALTER COLUMN es_in_situ TYPE INTEGER USING (CASE WHEN es_in_situ THEN 1 ELSE 0 END);",
    "ALTER TABLE solicitudes_master ALTER COLUMN es_in_situ SET DEFAULT 0;",
    
    # partidas
    "ALTER TABLE partidas ALTER COLUMN es_manual DROP DEFAULT;",
    "ALTER TABLE partidas ALTER COLUMN es_manual TYPE INTEGER USING (CASE WHEN es_manual THEN 1 ELSE 0 END);",
    "ALTER TABLE partidas ALTER COLUMN es_manual SET DEFAULT 0;",
    
    "ALTER TABLE partidas ALTER COLUMN es_no_realizable DROP DEFAULT;",
    "ALTER TABLE partidas ALTER COLUMN es_no_realizable TYPE INTEGER USING (CASE WHEN es_no_realizable THEN 1 ELSE 0 END);",
    "ALTER TABLE partidas ALTER COLUMN es_no_realizable SET DEFAULT 0;",
    
    # usuarios
    "ALTER TABLE usuarios ALTER COLUMN activo DROP DEFAULT;",
    "ALTER TABLE usuarios ALTER COLUMN activo TYPE INTEGER USING (CASE WHEN activo THEN 1 ELSE 0 END);",
    "ALTER TABLE usuarios ALTER COLUMN activo SET DEFAULT 1;"
]

for s in sqls:
    print("Executing:", s)
    c.execute(s)

conn.conn.commit()
print("Conversión completada con éxito.")

# Probar consultas
c.execute("SELECT count(*) FROM partidas WHERE es_no_realizable = 0")
print("Prueba SELECT partidas WHERE es_no_realizable = 0:", c.fetchone()[0])

c.execute("SELECT count(*) FROM solicitudes_master WHERE es_extranjero = 0")
print("Prueba SELECT solicitudes_master WHERE es_extranjero = 0:", c.fetchone()[0])

conn.close()
