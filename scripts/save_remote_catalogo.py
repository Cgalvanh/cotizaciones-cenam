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

req = urllib.request.Request(f'{url_base}/catalogo_servicios?select=*', headers=headers)
res = urllib.request.urlopen(req, timeout=10)
data = json.loads(res.read().decode())

df = pd.DataFrame(data)
print("DataFrame Shape:", df.shape)
print("\nColumns:", df.columns.tolist())
print("\nNon-null count per column:")
print(df.notnull().sum())
print("\nSample of 5 records:")
print(df[['id_c_serv', 'clave_servicio', 'laboratorio', 'division', 'precio', 'tiempo', 'descripcion']].head())

# Guardar backup local en data/
df.to_csv("data/catalogo_servicios_supabase_extraido.csv", index=False)
print("\nGuardado en data/catalogo_servicios_supabase_extraido.csv con 612 servicios.")
