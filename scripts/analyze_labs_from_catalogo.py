import json
import pandas as pd

df = pd.read_csv("data/catalogo_servicios_supabase_extraido.csv")
print("Total servicios cargados:", len(df))

# Agrupar por laboratorio
grouped = df.groupby(['division', 'laboratorio']).agg(
    total_servicios=('id_c_serv', 'count'),
    min_precio=('precio', 'min'),
    max_precio=('precio', 'max'),
    ejemplo_servicio=('descripcion', 'first')
).reset_index()

print("\n--- LABORATORIOS AGRUPADOS POR DIVISION (DE CATALOGO_SERVICIOS) ---")
print(grouped.to_string(index=False))
