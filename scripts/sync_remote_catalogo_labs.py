import urllib.request
import json
import pandas as pd

url_base = 'https://hgjbvfojjibcwespaxly.supabase.co/rest/v1'
key = 'sb_publishable_nxXsrifcSI7BbIk1FDBp1g_j43HtdDU'

headers = {
    'apikey': key,
    'Authorization': f'Bearer {key}',
    'Accept': 'application/json',
    'Range': '0-999'
}

# 1. Extraer laboratorios con las columnas autorizadas
COLUMNAS_LABORATORIO = 'id_uni,codigo,descripcion,id_division,id_area,activo,laboratorio'
req_lab = urllib.request.Request(f'{url_base}/laboratorios?select={COLUMNAS_LABORATORIO}', headers=headers)
res_lab = urllib.request.urlopen(req_lab, timeout=10)
labs_data = json.loads(res_lab.read().decode())
df_labs = pd.DataFrame(labs_data)
print(f"Total Laboratorios extraídos: {len(df_labs)}")
df_labs.to_csv("data/laboratorios_supabase_extraido.csv", index=False)

# 2. Extraer catálogo de servicios
req_serv = urllib.request.Request(f'{url_base}/catalogo_servicios?select=*', headers=headers)
res_serv = urllib.request.urlopen(req_serv, timeout=10)
serv_data = json.loads(res_serv.read().decode())
df_serv = pd.DataFrame(serv_data)
print(f"Total Servicios extraídos: {len(df_serv)}")
df_serv.to_csv("data/catalogo_servicios_supabase_extraido.csv", index=False)

# 3. Análisis de áreas y divisiones en laboratorios
print("\n--- ÁREAS EN LABORATORIOS (id_area) ---")
print(df_labs['id_area'].value_counts())

print("\n--- DIVISIONES EN LABORATORIOS (id_division) ---")
print(df_labs['id_division'].value_counts())

# 4. Cruce de laboratorios con catalogo_servicios
# En catalogo_servicios, la columna 'laboratorio' contiene el 'codigo' del laboratorio (ej. 'D014A', 'D011', 'F001', etc.)
# Cruce por df_serv['laboratorio'] == df_labs['codigo']
df_merged = df_serv.merge(df_labs, left_on='laboratorio', right_on='codigo', how='left', suffixes=('_serv', '_lab'))
matched = df_merged['codigo'].notnull().sum()
unmatched = df_merged['codigo'].isnull().sum()
print(f"\nServicios con laboratorio cruzado exitosamente: {matched} de {len(df_serv)}")
if unmatched > 0:
    print(f"Servicios sin match en laboratorios: {unmatched}")
    print("Laboratorios no encontrados en tabla laboratorios:", df_merged[df_merged['codigo'].isnull()]['laboratorio'].unique())

print("\n--- MUESTRA DEL CRUCE EXITOSO ---")
print(df_merged[['clave_servicio', 'laboratorio', 'descripcion_serv', 'precio', 'id_area', 'id_division', 'descripcion_lab']].head(10))
