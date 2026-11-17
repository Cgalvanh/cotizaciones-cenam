import pandas as pd

df_labs = pd.read_csv("data/laboratorios_supabase_extraido.csv")
df_serv = pd.read_csv("data/catalogo_servicios_supabase_extraido.csv")

# Filtrar laboratorios activos
# Si hay duplicados activos, tomar el último id_uni
labs_clean = df_labs[df_labs['activo'] == True].sort_values('id_uni').drop_duplicates(subset=['codigo'], keep='last')

# Cruce
df_merged = df_serv.merge(labs_clean, left_on='laboratorio', right_on='codigo', how='left', suffixes=('_serv', '_lab'))

print(f"Total Servicios: {len(df_serv)}")
print(f"Servicios cruzados con éxito: {df_merged['codigo'].notnull().sum()}")
unmatched = df_merged[df_merged['codigo'].isnull()]['laboratorio_serv'].unique()
print(f"Laboratorios sin match: {unmatched}")

# Mostrar agrupado por Área Técnica / id_area
print("\n--- SERVICIOS Y COSTOS POR ID_AREA ---")
area_summary = df_merged.groupby('id_area').agg(
    total_servicios=('id_c_serv', 'count'),
    total_labs=('codigo', 'nunique'),
    precio_min=('precio', 'min'),
    precio_prom=('precio', 'mean'),
    precio_max=('precio', 'max')
)
print(area_summary)

print("\n--- DETALLE DE LABORATORIOS IDENTIFICADOS ---")
labs_in_serv = df_merged[['id_area', 'id_division_lab', 'codigo', 'descripcion_lab']].drop_duplicates().sort_values(['id_area', 'codigo'])
print(labs_in_serv.to_string(index=False))
