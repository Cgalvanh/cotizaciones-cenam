import os, sys, pandas as pd
sys.path.insert(0, os.path.abspath('.'))
from dotenv import load_dotenv
load_dotenv('.env')

from nube_segura import cloud_db as cdb

conn, engine = cdb.get_db_connection()
c = conn.cursor()

print(f'Connected via engine: {engine}')
if engine == 'POSTGRES':
    print('Updating PostgreSQL Supabase tables...')
    c.execute('''
    CREATE TABLE IF NOT EXISTS areas_tecnicas (
        clave VARCHAR(20) PRIMARY KEY,
        nombre VARCHAR(255) NOT NULL,
        id_area INTEGER,
        direccion VARCHAR(255)
    );
    ''')
    
    try:
        c.execute('ALTER TABLE areas_tecnicas ADD COLUMN id_area INTEGER;')
    except Exception:
        pass
    try:
        c.execute('ALTER TABLE areas_tecnicas ADD COLUMN direccion VARCHAR(255);')
    except Exception:
        pass
        
    df_areas = pd.read_csv('data/areas_tecnicas.csv')
    for _, r in df_areas.iterrows():
        c.execute('''
        INSERT INTO areas_tecnicas (clave, nombre, id_area, direccion)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (clave) DO UPDATE 
        SET nombre = EXCLUDED.nombre, id_area = EXCLUDED.id_area, direccion = EXCLUDED.direccion;
        ''', (str(r['clave']), str(r['nombre']), int(r['id_area']), str(r['direccion'])))

    # First update catalogo_servicios references to new keys
    mapping_old = {
        'AT-01': '740', 'AT-02': '410', 'AT-03': '440', 'AT-04': '430',
        'AT-05': '420', 'AT-06': '520', 'AT-07': '730', 'AT-08': '720',
        'AT-09': '710', 'AT-10': '510', 'AT-11': '700', 'AT-12': '630',
        'AT-13': '620', 'AT-14': '810'
    }
    for old_k, new_k in mapping_old.items():
        c.execute('''
        UPDATE catalogo_servicios 
        SET clave_area = %s, codigo_division = %s 
        WHERE clave_area = %s
        ''', (new_k, int(new_k), old_k))
        
    c.execute('''
    UPDATE catalogo_servicios
    SET clave_area = CAST(codigo_division AS VARCHAR)
    WHERE codigo_division IS NOT NULL AND codigo_division > 0
    ''')

    # Also update any sub_solicitudes_at with old AT-XX keys if present
    for old_k, new_k in mapping_old.items():
        c.execute('''
        UPDATE sub_solicitudes_at SET clave_area = %s WHERE clave_area = %s
        ''', (new_k, old_k))

    c.execute("DELETE FROM areas_tecnicas WHERE clave LIKE 'AT-%'")
    
    conn.commit()
    print('Supabase PostgreSQL updated successfully!')
    
    c.execute('SELECT clave, nombre FROM areas_tecnicas ORDER BY clave')
    for r in c.fetchall():
        print('  ', r['clave'], ':', r['nombre'])
conn.close()
