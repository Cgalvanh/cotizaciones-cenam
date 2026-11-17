import urllib.request
import json
from collections import defaultdict

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

div_labs = defaultdict(set)
lab_samples = {}

for row in data:
    div = row.get('division')
    lab = row.get('laboratorio')
    div_labs[div].add(lab)
    if lab not in lab_samples:
        lab_samples[lab] = row

print("="*60)
print(f"CATALOGO EXTRAIDO DE SUPABASE: {len(data)} SERVICIOS")
print("="*60)

print("\n--- DIVISIONES Y SUS LABORATORIOS ---")
for div in sorted(div_labs.keys(), key=lambda x: str(x)):
    labs = sorted(div_labs[div], key=lambda x: str(x))
    print(f"División {div} ({len(labs)} labs): {', '.join(labs)}")

print("\n--- DETALLE DE LABORATORIOS, SERVICIOS Y COSTOS ---")
for lab in sorted(lab_samples.keys(), key=lambda x: str(x)):
    r = lab_samples[lab]
    desc = (r.get('descripcion') or '')[:45]
    p = r.get('precio') or 0.0
    t = r.get('tiempo') or 5
    cs = r.get('clave_servicio') or ''
    dv = r.get('division')
    print(f"Lab {lab:6} | Div {dv} | Clave: {cs:18} | Costo: ${p:9,.2f} | Días: {t:2} | Desc: {desc}...")
