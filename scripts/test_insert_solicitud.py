import sys, os
from datetime import datetime
sys.path.insert(0, os.path.abspath("nube_segura"))
import cloud_db as cdb

conn, engine = cdb.get_db_connection()
c = conn.cursor()

no_solicitud = "2026009PR"
no_folio = "0009-2026PR"
cliente = "SEÑALIZACION Y CONTROL DEL SURESTE"
representante = "ROSA DE LA CRUZ"
telefono = "938 105 7208"
correo = "compras@secont.mx"
rfc = "SCS-121208-QK4"
pais = "MÉXICO"
es_extranjero = False
aplica_iva = True
es_in_situ = False
now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
vig_str = f"{datetime.now().year}-12-31"

print(f"Probando INSERT en solicitudes_master en motor: {engine}...")
c.execute("""
INSERT INTO solicitudes_master (
    no_solicitud, no_folio, version, cliente, representante, telefono, correo, rfc, pais,
    es_extranjero, aplica_iva, fecha_recepcion, fecha_emision, vigencia, estado, es_in_situ
) VALUES (?, ?, 1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'TURNADA', ?)
""", (
    no_solicitud, no_folio, cliente, representante, telefono, correo, rfc, pais,
    1 if es_extranjero else 0, 0 if (es_extranjero and aplica_iva) else (1 if aplica_iva else 0),
    now_str, datetime.now().strftime("%Y-%m-%d"), vig_str, 1 if es_in_situ else 0
))

sol_id = c.lastrowid
print("INSERT exitoso! ID generado en Supabase:", sol_id)
conn.commit()

# Limpiar fila de prueba
c.execute("DELETE FROM solicitudes_master WHERE id = ?", (sol_id,))
conn.commit()
conn.close()
print("Prueba completada al 100% sin errores.")
