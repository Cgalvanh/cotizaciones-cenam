import pandas as pd

df_labs = pd.read_csv("data/laboratorios_supabase_extraido.csv")
print("Total rows in df_labs:", len(df_labs))
print("Unique codigos in df_labs:", df_labs['codigo'].nunique())

# Check duplicates
dups = df_labs[df_labs.duplicated(subset=['codigo'], keep=False)]
if not dups.empty:
    print(f"\nHay {len(dups)} filas duplicadas por 'codigo'. Ejemplo:")
    print(dups.sort_values('codigo')[['id_uni', 'codigo', 'descripcion', 'id_division', 'id_area', 'activo', 'laboratorio']].head(10))

# Filtrar solo los activos
activos = df_labs[df_labs['activo'] == True]
print(f"\nLaboratorios activos: {len(activos)} (Únicos: {activos['codigo'].nunique()})")
