import pandas as pd

df_old = pd.read_csv("data/catalogo_servicios.csv")
df_new = pd.read_csv("data/catalogo_servicios_completo_cenam.csv")

print(f"Catálogo antiguo: {len(df_old)} servicios")
print(f"Catálogo nuevo (Supabase): {len(df_new)} servicios")

print("\nÁreas en catálogo antiguo:")
print(df_old['Clave_Area'].value_counts())

print("\nÁreas en catálogo nuevo (Supabase):")
print(df_new['clave_area'].value_counts())

# Verificar claves
print("\nEjemplo de claves antiguo:", df_old['Clave_Servicio'].head(5).tolist())
print("Ejemplo de claves nuevo:", df_new['clave_servicio'].head(5).tolist())
