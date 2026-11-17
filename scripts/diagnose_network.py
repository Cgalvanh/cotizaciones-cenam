import socket
import sys

def test_tcp(host, port, timeout=2.0):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    try:
        s.connect((host, port))
        s.close()
        return True, "OPEN"
    except socket.timeout:
        return False, "TIMEOUT"
    except ConnectionRefusedError:
        return False, "REFUSED"
    except Exception as e:
        return False, str(e)

print("--- PROBANDO CONECTIVIDAD DE RED ---", flush=True)

# 1. Probar si el puerto 5432 outbound está abierto en general
test_targets = [
    ("google.com", 80),
    ("google.com", 443),
    ("aws-0-us-east-1.pooler.supabase.com", 5432),
    ("aws-0-us-east-1.pooler.supabase.com", 6543),
    ("aws-0-us-east-2.pooler.supabase.com", 5432),
    ("aws-0-us-east-2.pooler.supabase.com", 6543),
    ("aws-0-us-west-1.pooler.supabase.com", 5432),
    ("aws-0-us-west-1.pooler.supabase.com", 6543),
    ("aws-0-us-west-2.pooler.supabase.com", 5432),
    ("aws-0-us-west-2.pooler.supabase.com", 6543),
    ("aws-0-sa-east-1.pooler.supabase.com", 5432),
    ("aws-0-sa-east-1.pooler.supabase.com", 6543),
]

for host, port in test_targets:
    ok, status = test_tcp(host, port, timeout=2.0)
    print(f"{host}:{port} -> {status}", flush=True)
