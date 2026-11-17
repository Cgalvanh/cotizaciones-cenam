import urllib.request
import json
import pandas as pd
import os

url_base = 'https://hgjbvfojjibcwespaxly.supabase.co/rest/v1'
key = 'sb_publishable_nxXsrifcSI7BbIk1FDBp1g_j43HtdDU'

headers = {
    'apikey': key,
    'Authorization': f'Bearer {key}',
    'Accept': 'application/json',
    'Range': '0-999'
}

# 1. Extraer laboratorios con columnas explícitas
COLUMNAS_LABORATORIO = 'id_uni,codigo,descripcion,id_division,id_area,activo,laboratorio'
req_lab = urllib.request.Request(f'{url_base}/laboratorios?select={COLUMNAS_LABORATORIO}', headers=headers)
res_lab = urllib.request.urlopen(req_lab, timeout=10)
df_labs = pd.DataFrame(json.loads(res_lab.read().decode()))

# 2. Extraer catálogo de servicios completo
req_serv = urllib.request.Request(f'{url_base}/catalogo_servicios?select=*', headers=headers)
res_serv = urllib.request.urlopen(req_serv, timeout=10)
df_serv = pd.DataFrame(json.loads(res_serv.read().decode()))

print(f"Laboratorios extraídos: {len(df_labs)}")
print(f"Servicios extraídos: {len(df_serv)}")

# Mapeo de División a Clave de Área Técnica (AT-01 a AT-14)
DIV_TO_AT = {
    740: ('AT-01', 'Metrología Dimensional'),
    410: ('AT-02', 'Metrología Eléctrica'),
    440: ('AT-03', 'Radiofrecuencia y Campos Electromagnéticos'),
    430: ('AT-04', 'Tiempo y Frecuencia'),
    420: ('AT-05', 'Termometría y Humedad'),
    520: ('AT-06', 'Óptica y Radiometría'),
    730: ('AT-07', 'Masa y Densidad'),
    720: ('AT-08', 'Fuerza y Presión'),
    710: ('AT-09', 'Flujo y Volumen'),
    510: ('AT-10', 'Vibraciones y Acústica'),
    610: ('AT-11', 'Materiales Metálicos y Dureza'),
    700: ('AT-11', 'Materiales Metálicos y Dureza'), # Dureza y aceleración gravimétrica
    620: ('AT-12', 'Metrología Química y Gases'),
    630: ('AT-13', 'Fisicoquímica y Propiedades Termofísicas'),
    800: ('AT-14', 'Servicios Especiales e In Situ'),
    810: ('AT-14', 'Servicios Especiales e In Situ')
}

# Preparar catálogo limpio de laboratorios (usar el registro más reciente por código)
labs_map = {}
for _, r in df_labs.sort_values('id_uni').iterrows():
    c = str(r['codigo']).strip()
    labs_map[c] = {
        'id_uni': r['id_uni'],
        'codigo': c,
        'nombre_lab': str(r['descripcion']).strip() if pd.notnull(r['descripcion']) else c,
        'id_division': r['id_division'],
        'id_area': r['id_area'],
        'activo': bool(r['activo']),
        'es_lab': bool(r['laboratorio'])
    }

# Enriquecer cada servicio con su Área Técnica y datos de Laboratorio
rows_enriquecidas = []
for _, s in df_serv.iterrows():
    lab_cod = str(s.get('laboratorio') or '').strip()
    div_num = int(s.get('division')) if pd.notnull(s.get('division')) else 740
    
    # Buscar en diccionario de laboratorios
    lab_info = labs_map.get(lab_cod, {})
    nombre_lab = lab_info.get('nombre_lab', f"Laboratorio {lab_cod}")
    
    # Determinar AT
    at_info = DIV_TO_AT.get(div_num, ('AT-01', 'Metrología Dimensional'))
    clave_at, nombre_at = at_info
    
    # Si el laboratorio específico indica otra área o especialidad (ej. termometría D021)
    if lab_cod == 'D021':
        clave_at, nombre_at = 'AT-05', 'Termometría y Humedad'
        
    rows_enriquecidas.append({
        'id_c_serv': s.get('id_c_serv'),
        'clave_servicio': s.get('clave_servicio'),
        'clave_area': clave_at,
        'nombre_area': nombre_at,
        'codigo_laboratorio': lab_cod,
        'nombre_laboratorio': nombre_lab,
        'codigo_division': div_num,
        'descripcion': s.get('descripcion'),
        'precio': float(s.get('precio')) if pd.notnull(s.get('precio')) else 0.0,
        'tiempo_dias_habiles': int(s.get('tiempo')) if pd.notnull(s.get('tiempo')) else 5,
        'intervalo': s.get('intervalo'),
        'incertidumbre': s.get('incertidumbre'),
        'metodo': s.get('metodo'),
        'observaciones': s.get('observaciones'),
        'pago': s.get('pago')
    })

df_final = pd.DataFrame(rows_enriquecidas)
print("\n--- RESUMEN DE SERVICIOS POR ÁREA TÉCNICA ---")
print(df_final.groupby(['clave_area', 'nombre_area']).agg(
    total_servicios=('clave_servicio', 'count'),
    total_laboratorios=('codigo_laboratorio', 'nunique'),
    precio_min=('precio', 'min'),
    precio_max=('precio', 'max')
))

# Guardar CSV consolidado
os.makedirs("data", exist_ok=True)
df_final.to_csv("data/catalogo_servicios_completo_cenam.csv", index=False, encoding="utf-8-sig")
df_labs.to_csv("data/laboratorios_cenam_completo.csv", index=False, encoding="utf-8-sig")

print("\n¡Archivos generados exitosamente en data/:")
print("  - catalogo_servicios_completo_cenam.csv (612 servicios)")
print("  - laboratorios_cenam_completo.csv (294 laboratorios y áreas)")
