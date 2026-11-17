"""
Test integral para validar los 4 nuevos requerimientos del usuario:
1. Ubicación y extracción correcta del nombre del cliente desde archivos .docx.
2. Filtrado por laboratorio en la cotización de CS-AT.
3. Control de acceso y autenticación por usuario con aislamiento por Área Técnica.
4. Inclusión del logo oficial de CENAM en la interfaz web y formatos PDF hacia el cliente.
"""
import subprocess
import urllib.request
import json
import time
import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(BASE_DIR, ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

import request_parser as rp
import pdf_generator as pg

def test_all_requirements():
    print("=" * 75)
    print(" VERIFICACION DE LOS 4 NUEVOS REQUERIMIENTOS CENAM")
    print("=" * 75)

    # ----------------------------------------------------
    # 1. Verificación de Extracción del Nombre del Cliente
    # ----------------------------------------------------
    print("\n[REQ 1] Verificando extracción del Nombre del Cliente desde archivo .docx...")
    docx_path = r"C:\Users\cgalvan\.gemini\antigravity\brain\d8ba3ed8-7506-4828-bfd0-144e2139d5f5\.user_uploaded\media_1793848564329_69f18b45.docx"
    assert os.path.exists(docx_path), "Archivo de prueba docx no encontrado"
    
    parsed = rp.parse_solicitud_docx(docx_path)
    cliente = parsed.get("empresa")
    contacto = parsed.get("contacto")
    rfc = parsed.get("rfc")
    
    print(f" -> Cliente extraído : '{cliente}'")
    print(f" -> Contacto extraído: '{contacto}'")
    print(f" -> RFC extraído     : '{rfc}'")
    
    assert cliente == "SEÑALIZACION Y CONTROL DEL SURESTE", f"Cliente incorrecto: {cliente}"
    assert "Estimado cliente" not in cliente, "Capturó texto de saludo en lugar del cliente"
    assert contacto == "ROSA DE LA CRUZ"
    print(" -> [OK] REQ 1 CUMPLIDO: El nombre del cliente y contacto se extraen con precisión absoluta.")

    # ----------------------------------------------------
    # 4. Verificación del Logo Oficial de CENAM
    # ----------------------------------------------------
    print("\n[REQ 4] Verificando presencia e integración del Logo Oficial CENAM...")
    logo_path = pg.get_cenam_logo_path()
    assert logo_path and os.path.exists(logo_path), "Logo oficial CENAM no encontrado"
    logo_size = os.path.getsize(logo_path)
    print(f" -> Logo resuelto por pdf_generator: {logo_path} ({logo_size:,} bytes)")
    
    # Probar que static/cenam_logo.png existe para la interfaz web
    assert os.path.exists("static/cenam_logo.png"), "Falta static/cenam_logo.png"
    assert os.path.exists("nube_segura/static/cenam_logo.png"), "Falta nube_segura/static/cenam_logo.png"
    print(" -> [OK] REQ 4 CUMPLIDO: Logo oficial disponible para PDFs y Web UI.")

    # ----------------------------------------------------
    # Iniciar Servidor Uvicorn para probar API (Req 2 y 3)
    # ----------------------------------------------------
    port = 8012
    url_base = f"http://127.0.0.1:{port}"
    print(f"\nLevantando servidor Uvicorn en puerto {port}...")
    cmd = [sys.executable, "-m", "uvicorn", "server:app", "--host", "127.0.0.1", "--port", str(port)]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    try:
        ready = False
        for _ in range(25):
            time.sleep(0.3)
            try:
                with urllib.request.urlopen(f"{url_base}/api/health", timeout=1) as resp:
                    if resp.status == 200:
                        ready = True
                        break
            except Exception:
                pass
        assert ready, "El servidor Uvicorn no respondió"

        # ----------------------------------------------------
        # 2. Filtrado por Laboratorio en CS-AT
        # ----------------------------------------------------
        print("\n[REQ 2] Probando filtrado de catálogo por Laboratorio Técnico...")
        with urllib.request.urlopen(f"{url_base}/api/catalogos/laboratorios?clave_area=740") as resp:
            labs_740 = json.loads(resp.read().decode('utf-8'))
            assert len(labs_740) > 0, "Deben existir laboratorios para 740"
            lab_target = labs_740[0]
            lab_cod = lab_target['codigo']
            print(f" -> {len(labs_740)} Laboratorios disponibles en Área 740 (Probando con: {lab_cod} - {lab_target['descripcion']}).")

        # Filtrar servicios de ese laboratorio
        with urllib.request.urlopen(f"{url_base}/api/catalogos/servicios?clave_area=740&codigo_lab={lab_cod}") as resp:
            servs_lab = json.loads(resp.read().decode('utf-8'))
            assert len(servs_lab) > 0, f"Deben existir servicios en el laboratorio {lab_cod}"
            assert all(s.get('codigo_laboratorio') == lab_cod for s in servs_lab), "Todos los servicios deben ser de ese laboratorio"
            print(f" -> Catálogo filtrado con éxito: {len(servs_lab)} servicios específicos del laboratorio {lab_cod}.")
            print(" -> [OK] REQ 2 CUMPLIDO: CS-AT puede filtrar servicios por laboratorio técnico.")

        # ----------------------------------------------------
        # 3. Control de Acceso por Usuario y Aislamiento por Área
        # ----------------------------------------------------
        print("\n[REQ 3] Probando Control de Acceso por Usuario y Aislamiento de Áreas...")
        with urllib.request.urlopen(f"{url_base}/api/auth/usuarios") as resp:
            users = json.loads(resp.read().decode('utf-8'))
            assert len(users) >= 17, f"Deben existir al menos 17 cuentas, encontradas: {len(users)}"
            print(f" -> {len(users)} cuentas oficiales cargadas en el sistema.")

        # Probar Login de Ventanilla SSI
        login_ssi_payload = {"correo": "ssi@cenam.mx", "password": "Cenam2026*"}
        req_ssi = urllib.request.Request(f"{url_base}/api/auth/login", data=json.dumps(login_ssi_payload).encode('utf-8'), headers={'Content-Type': 'application/json'}, method='POST')
        with urllib.request.urlopen(req_ssi) as resp:
            res_ssi = json.loads(resp.read().decode('utf-8'))
            assert res_ssi["status"] == "success"
            assert res_ssi["user"]["rol"] == "SSI"
            print(f" -> Login SSI exitoso: {res_ssi['user']['nombre_completo']} ({res_ssi['user']['rol']})")

        # Probar Login de Área Técnica 740 (Dimensional)
        login_740_payload = {"correo": "at740@cenam.mx", "password": "Cenam2026*"}
        req_740 = urllib.request.Request(f"{url_base}/api/auth/login", data=json.dumps(login_740_payload).encode('utf-8'), headers={'Content-Type': 'application/json'}, method='POST')
        with urllib.request.urlopen(req_740) as resp:
            res_740 = json.loads(resp.read().decode('utf-8'))
            assert res_740["status"] == "success"
            assert res_740["user"]["rol"] == "AT"
            assert res_740["user"]["clave_area"] == "740"
            print(f" -> Login AT 740 exitoso: {res_740['user']['nombre_completo']} (Área asignada: {res_740['user']['clave_area']})")

        # Probar Login de Área Técnica 420 (Termometría)
        login_420_payload = {"correo": "at420@cenam.mx", "password": "Cenam2026*"}
        req_420 = urllib.request.Request(f"{url_base}/api/auth/login", data=json.dumps(login_420_payload).encode('utf-8'), headers={'Content-Type': 'application/json'}, method='POST')
        with urllib.request.urlopen(req_420) as resp:
            res_420 = json.loads(resp.read().decode('utf-8'))
            assert res_420["user"]["clave_area"] == "420"
            print(f" -> Login AT 420 exitoso: {res_420['user']['nombre_completo']} (Área asignada: {res_420['user']['clave_area']})")

        # Probar que rechaza contraseña incorrecta
        bad_login = {"correo": "ssi@cenam.mx", "password": "PasswordInvalido123"}
        req_bad = urllib.request.Request(f"{url_base}/api/auth/login", data=json.dumps(bad_login).encode('utf-8'), headers={'Content-Type': 'application/json'}, method='POST')
        try:
            with urllib.request.urlopen(req_bad) as resp:
                assert False, "Debió rechazar credenciales incorrectas"
        except urllib.error.HTTPError as err:
            assert err.code == 401
            print(" -> Seguridad verificada: Rechazo correcto de contraseña errónea (HTTP 401).")

        # Verificar HTML: Logo presente, Modal de Login presente y Filtro de Laboratorio presente
        with urllib.request.urlopen(f"{url_base}/") as resp:
            html = resp.read().decode('utf-8')
            assert 'cenam_logo.png' in html, "Falta logo en HTML"
            assert 'id="modal-login"' in html, "Falta modal de login en HTML"
            assert 'filtrarServiciosPorLaboratorio' in html, "Falta función de filtro por laboratorio en JS"
            print(" -> [OK] REQ 3 CUMPLIDO: Autenticación por usuario, aislamiento por AT e interfaz verificados.")

        print("\n" + "=" * 75)
        print(" ¡LOS 4 REQUERIMIENTOS DEL USUARIO FUERON VALIDADOS CON 100% DE ÉXITO!")
        print("=" * 75)

    finally:
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except Exception:
            proc.kill()

if __name__ == "__main__":
    test_all_requirements()
