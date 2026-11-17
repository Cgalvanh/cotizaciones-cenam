import pandas as pd

df_labs = pd.read_csv("data/laboratorios_supabase_extraido.csv")
print("Total rows:", len(df_labs))

# Ver filas donde 'laboratorio' es False (suelen ser Direcciones o Áreas)
areas_org = df_labs[df_labs['laboratorio'] == False]
print("\n--- DIRECCIONES / ÁREAS ENCONTRADAS (laboratorio == False) ---")
print(areas_org[['id_uni', 'codigo', 'descripcion', 'id_division', 'id_area', 'activo']].to_string(index=False))

# Ver laboratorios por división
print("\n--- RESUMEN POR ID_DIVISION ---")
summary_div = df_labs.groupby(['id_area', 'id_division']).agg(
    total_labs=('codigo', 'count'),
    ejemplo=('descripcion', 'first')
).reset_index()
print(summary_div.to_string(index=False))
