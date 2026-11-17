import pandas as pd

df = pd.read_csv('data/laboratorios_cenam_completo.csv')
for div, g in df.groupby('id_division'):
    area_val = g['id_area'].iloc[0] if not g['id_area'].empty else 'N/A'
    print(f"\nDivisión {int(div) if pd.notnull(div) else 'N/A'} (Área {int(area_val) if pd.notnull(area_val) else 'N/A'}):")
    for _, r in g.head(4).iterrows():
        cod = r['codigo']
        desc = str(r['descripcion'])[:60]
        print(f"   [{cod}] {desc}")
