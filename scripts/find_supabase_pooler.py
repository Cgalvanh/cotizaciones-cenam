import psycopg2
import sys

regions = [
    'us-east-1', 'us-east-2', 'us-west-1', 'us-west-2',
    'sa-east-1', 'ca-central-1', 'eu-central-1', 'eu-west-1'
]
pwd = 'f87*WRP5n3kG3zzX'
ref = 'lmvpzqniqjhdtjmmxvdg'

# Supabase pooler username formats:
# 1) postgres.lmvpzqniqjhdtjmmxvdg
# 2) postgres (if not pooler or specific mode)
for reg in regions:
    host = f"aws-0-{reg}.pooler.supabase.com"
    for port in [6543, 5432]:
        for user in [f"postgres.{ref}"]:
            try:
                print(f"Probando {host}:{port} con usuario {user}...", end=" ", flush=True)
                conn = psycopg2.connect(
                    host=host,
                    port=port,
                    user=user,
                    password=pwd,
                    dbname="postgres",
                    sslmode="require",
                    connect_timeout=4
                )
                print("¡CONEXION EXITOSA!")
                cur = conn.cursor()
                cur.execute("SELECT current_database(), current_user;")
                print("Datos:", cur.fetchone())
                conn.close()
                sys.exit(0)
            except Exception as e:
                err_msg = str(e).strip().replace("\n", " ")
                print(f"ERROR: {err_msg[:80]}")
