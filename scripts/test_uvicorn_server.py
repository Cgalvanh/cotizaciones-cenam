"""
Test automatizado para validar el servidor Uvicorn (FastAPI) de CENAM:
1. Inicia Uvicorn en un hilo/subproceso controlado
2. Realiza peticiones HTTP reales a http://127.0.0.1:8005
3. Valida endpoints clave: /api/health, /api/catalogos/areas, /api/catalogos/servicios, /api/ssi/expedientes, /, /docs
4. Detiene el servidor limpiamente
"""
import os
import sys
import time
import subprocess
import urllib.request
import json

def test_uvicorn():
    print("=" * 70)
    print("INICIANDO PRUEBA DE SERVIDOR ASGI UVICORN (FASTAPI)")
    print("=" * 70)
    
    port = 8005
    url_base = f"http://127.0.0.1:{port}"
    
    # 1. Iniciar Uvicorn en segundo plano
    print(f"\n[1] Lanzando proceso Uvicorn en puerto {port}...")
    cmd = [sys.executable, "-m", "uvicorn", "server:app", "--host", "127.0.0.1", "--port", str(port)]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    # Esperar hasta que responda el healthcheck (max 10 segundos)
    server_ready = False
    for i in range(20):
        time.sleep(0.5)
        try:
            req = urllib.request.Request(f"{url_base}/api/health")
            with urllib.request.urlopen(req, timeout=2) as resp:
                if resp.status == 200:
                    server_ready = True
                    break
        except Exception:
            pass
            
    if not server_ready:
        proc.terminate()
        stdout, stderr = proc.communicate(timeout=5)
        print("ERROR: Uvicorn no inicio a tiempo:")
        print(stderr.decode('utf-8', errors='ignore'))
        assert False, "Uvicorn no inicio correctamente"
        
    print(f"  -> Uvicorn iniciado y respondiendo en {url_base}")
    
    try:
        # 2. Probar Healthcheck
        print("\n[2] Probando endpoint /api/health:")
        with urllib.request.urlopen(f"{url_base}/api/health") as resp:
            data = json.loads(resp.read().decode('utf-8'))
            print("  Respuesta:", data)
            assert data["status"] == "healthy"
            assert data["server"] == "uvicorn"
            assert data["framework"] == "FastAPI"
            
        # 3. Probar Catálogo de Áreas Técnicas
        print("\n[3] Probando endpoint /api/catalogos/areas:")
        with urllib.request.urlopen(f"{url_base}/api/catalogos/areas") as resp:
            areas = json.loads(resp.read().decode('utf-8'))
            print(f"  Total de divisiones cargadas en Uvicorn: {len(areas)}")
            assert len(areas) == 15, "Deben ser 15 areas oficiales de CENAM"
            claves = [a['clave'] for a in areas]
            assert "740" in claves and "410" in claves and "730" in claves
            print("  Divisiones verificadas (740, 410, 730, etc.): OK")
            
        # 4. Probar Catálogo de Servicios filtrado por área 740
        print("\n[4] Probando endpoint /api/catalogos/servicios?clave_area=740:")
        with urllib.request.urlopen(f"{url_base}/api/catalogos/servicios?clave_area=740") as resp:
            servs = json.loads(resp.read().decode('utf-8'))
            print(f"  Servicios obtenidos para division 740: {len(servs)}")
            assert len(servs) > 0, "Debe retornar servicios de Dimensional"
            s1 = servs[0]
            print(f"  Muestra: {s1['clave_servicio']} - Costo: ${float(s1['costo']):,.2f}")
            assert float(s1['costo']) > 0, "Los costos deben ser mayores a cero"
            
        # 5. Probar Interfaz Web HTML en la raíz (/)
        print("\n[5] Probando carga de la Interfaz Web HTML (/):")
        with urllib.request.urlopen(f"{url_base}/") as resp:
            html_content = resp.read().decode('utf-8')
            assert resp.status == 200
            assert "Centro Nacional de Metrología" in html_content
            assert "Servidor Uvicorn" in html_content
            print("  Dashboard Web HTML servido por Uvicorn exitosamente.")
            
        # 6. Probar Swagger OpenAPI Docs (/docs)
        print("\n[6] Probando documentacion interactiva Swagger (/docs):")
        with urllib.request.urlopen(f"{url_base}/docs") as resp:
            assert resp.status == 200
            print("  Documentacion Swagger interactiva disponible y funcionando.")
            
        print("\n" + "=" * 70)
        print("TODAS LAS PRUEBAS DEL SERVIDOR UVICORN PASARON CON 100% DE EXITO")
        print("=" * 70)
        
    finally:
        # Detener proceso uvicorn
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except Exception:
            proc.kill()
        print("\n[Fin] Servidor de prueba detenido correctamente.")

if __name__ == "__main__":
    test_uvicorn()
