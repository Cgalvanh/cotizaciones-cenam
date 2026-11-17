import psycopg2

pwd = 'f87*WRP5n3kG3zzX'
ref = 'lmvpzqniqjhdtjmmxvdg'

configs = [
    # (host, port, user, dbname)
    ("aws-0-us-east-1.pooler.supabase.com", 6543, f"postgres.{ref}", "postgres"),
    ("aws-0-us-east-1.pooler.supabase.com", 5432, f"postgres.{ref}", "postgres"),
    ("aws-0-us-east-1.pooler.supabase.com", 6543, "postgres", "postgres"),
    ("aws-0-us-east-1.pooler.supabase.com", 5432, "postgres", "postgres"),
]

for host, port, user, db in configs:
    print(f"\n--- Probando host={host}, port={port}, user={user}, db={db} ---")
    for sslmode in ['require', 'prefer', 'allow']:
        try:
            print(f"  sslmode={sslmode}...", end=" ", flush=True)
            conn = psycopg2.connect(
                host=host,
                port=port,
                user=user,
                password=pwd,
                dbname=db,
                sslmode=sslmode,
                connect_timeout=4
            )
            print("¡EXITO!")
            cur = conn.cursor()
            cur.execute("SELECT 1;")
            print("  Query result:", cur.fetchone())
            conn.close()
            break
        except Exception as e:
            print(f"Error: {e}")
