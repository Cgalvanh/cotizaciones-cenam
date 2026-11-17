"""
Test integral de extremo a extremo para validar el Servidor ASGI Uvicorn (FastAPI) de CENAM:
Verifica:
1. Sintaxis limpia de JavaScript y CSS embebido (renderizado offline/online sin dependencias rotas)
2. Ciclo de vida completo: Creación de expediente -> AT Cotiza -> Quality Gate -> Emisión SSI -> Aceptación -> Programación Fechas -> PDFs Oficiales Carta -> Limpieza Estado Cero
"""
import subprocess
import urllib.request
import json
import time
import os
import sys

def run_e2e_uvicorn_test():
    print("=" * 75)
    print(" INICIANDO TEST END-TO-END DE SERVIDOR UVICORN CENAM")
    print("=" * 75)

    port = 8010
    url_base = f"http://127.0.0.1:{port}"

    # 1. Iniciar servidor
    print(f"\n[1] Levantando servidor Uvicorn en puerto {port}...")
    cmd = [sys.executable, "-m", "uvicorn", "server:app", "--host", "127.0.0.1", "--port", str(port)]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    ready = False
    for _ in range(25):
        time.sleep(0.4)
        try:
            req = urllib.request.Request(f"{url_base}/api/health")
            with urllib.request.urlopen(req, timeout=1) as resp:
                if resp.status == 200:
                    ready = True
                    break
        except Exception:
            pass

    if not ready:
        proc.terminate()
        _, err = proc.communicate(timeout=3)
        print("Error levantando Uvicorn:", err.decode('utf-8', errors='ignore'))
        sys.exit(1)

    print(f" -> Uvicorn respondiendo correctamente en {url_base}")

    try:
        # 2. Validar HTML y Sintaxis JS
        print("\n[2] Verificando interfaz HTML y sintaxis de JavaScript...")
        with urllib.request.urlopen(f"{url_base}/") as resp:
            html = resp.read().decode('utf-8')
            assert ".hidden { display: none !important; }" in html, "Falta CSS fallback para .hidden"
            assert "Centro Nacional de Metrología" in html
            print(" -> CSS de respaldo embebido verificado.")

            # Extraer JS y verificar con node
            s_start = html.find('<script>') + len('<script>')
            s_end = html.find('</script>', s_start)
            js = html[s_start:s_end]
            with open("temp_js_check.js", "w", encoding="utf-8") as f:
                f.write(js)
            res_node = subprocess.run(["node", "--check", "temp_js_check.js"], capture_output=True, text=True)
            if os.path.exists("temp_js_check.js"):
                os.remove("temp_js_check.js")
            assert res_node.returncode == 0, f"Error de sintaxis JS: {res_node.stderr}"
            print(" -> Sintaxis JavaScript verificada con Node.js: 0 ERRORES.")

        # 3. Validar Catálogos
        print("\n[3] Validando catálogos oficiales...")
        with urllib.request.urlopen(f"{url_base}/api/catalogos/areas") as resp:
            areas = json.loads(resp.read().decode('utf-8'))
            assert len(areas) == 15, "Deben existir 15 divisiones tecnicas"
            print(f" -> 15 Áreas técnicas oficiales cargadas.")

        with urllib.request.urlopen(f"{url_base}/api/catalogos/servicios?clave_area=740") as resp:
            servs = json.loads(resp.read().decode('utf-8'))
            assert len(servs) > 0, "Deben existir servicios en division 740"
            s0 = servs[0]
            print(f" -> {len(servs)} servicios encontrados para Área 740 (Muestra: {s0['clave_servicio']} - ${float(s0['costo']):,.2f}).")

        # 4. Crear expediente de prueba
        print("\n[4] Creando expediente de prueba (Alternativa 3)...")
        crear_payload = {
            "cliente": "METROLOGIA INDUSTRIAL MEXICANA S.A. DE C.V.",
            "representante": "Ing. Carlos Mendoza",
            "telefono": "55-1234-5678",
            "correo": "cmendoza@metrologia.mx",
            "rfc": "MIM901015AB1",
            "pais": "México",
            "instrumentos": [
                {
                    "desc": "Bloques patrón longitudinales de acero grado 0",
                    "marca": "Mitutoyo",
                    "modelo": "BM1-103",
                    "serie": "SN-88219",
                    "clave_area": "740",
                    "es_in_situ": 0
                }
            ]
        }
        data_bytes = json.dumps(crear_payload).encode('utf-8')
        req = urllib.request.Request(f"{url_base}/api/solicitudes/crear-manual", data=data_bytes, headers={'Content-Type': 'application/json'}, method='POST')
        with urllib.request.urlopen(req) as resp:
            res_crear = json.loads(resp.read().decode('utf-8'))
            assert res_crear["status"] == "success"
            folio = res_crear["data"]["no_folio"]
            sols = res_crear["data"]["solicitudes_creadas"]
            sol_id = sols[0]["solicitud_id"]
            no_sol = sols[0]["no_solicitud"]
            print(f" -> Expediente creado con éxito: Folio {folio}, Solicitud {no_sol} (ID {sol_id}).")

        # 5. Consultar bandeja de AT 740
        print("\n[5] Consultando bandeja de CS-AT Dimensional (740)...")
        with urllib.request.urlopen(f"{url_base}/api/at/solicitudes-pendientes/740") as resp:
            subs_at = json.loads(resp.read().decode('utf-8'))
            assert len(subs_at) > 0, "La solicitud debe aparecer en la bandeja de 740"
            target_sub = next(s for s in subs_at if s["no_folio"] == folio)
            sub_id = target_sub["sub_id"]
            partida_id = target_sub["partidas"][0]["id"]
            print(f" -> Solicitud recibida en AT 740: SubSolicitud ID {sub_id}, Partida ID {partida_id}.")

        # 6. Quality Gate: Probar que rechaza cotización con precio $0.00
        print("\n[6] Probando Quality Gate de Precios (Rechazo de $0.00)...")
        bad_payload = {
            "sub_solicitud_id": sub_id,
            "partidas": [
                {"id": partida_id, "clave_servicio": "", "precio_unitario": 0.0, "cantidad": 1, "es_no_realizable": 0}
            ]
        }
        bad_bytes = json.dumps(bad_payload).encode('utf-8')
        req_bad = urllib.request.Request(f"{url_base}/api/at/aprobar-sub-solicitud", data=bad_bytes, headers={'Content-Type': 'application/json'}, method='POST')
        try:
            with urllib.request.urlopen(req_bad) as resp:
                assert False, "Debió rechazar cotización con precio 0"
        except urllib.error.HTTPError as err:
            assert err.code == 400
            print(" -> Quality Gate funcionó: Rechazó correctamente la partida sin precio (HTTP 400).")

        # 7. Asignar servicio oficial y aprobar en AT
        print("\n[7] Aprobando cotización con servicio y precio oficial...")
        ok_payload = {
            "sub_solicitud_id": sub_id,
            "partidas": [
                {
                    "id": partida_id,
                    "clave_servicio": s0["clave_servicio"],
                    "descripcion_servicio": s0["supuesto"],
                    "precio_unitario": float(s0["costo"]),
                    "cantidad": 1,
                    "comentarios_ssi": "Revisado con patrón de cuarzo",
                    "comentarios_cliente": "Entregar desmagnetizado y limpio",
                    "es_no_realizable": 0
                }
            ]
        }
        ok_bytes = json.dumps(ok_payload).encode('utf-8')
        req_ok = urllib.request.Request(f"{url_base}/api/at/aprobar-sub-solicitud", data=ok_bytes, headers={'Content-Type': 'application/json'}, method='POST')
        with urllib.request.urlopen(req_ok) as resp:
            assert resp.status == 200
            print(" -> Cotización aprobada por AT y turnada a SSI.")

        # 8. Asignar Número de Cotización en SSI
        print("\n[8] Asignando Número de Cotización Oficial en SSI...")
        cot_payload = {"solicitud_id": sol_id}
        cot_bytes = json.dumps(cot_payload).encode('utf-8')
        req_cot = urllib.request.Request(f"{url_base}/api/ssi/asignar-numero-cotizacion", data=cot_bytes, headers={'Content-Type': 'application/json'}, method='POST')
        with urllib.request.urlopen(req_cot) as resp:
            cot_res = json.loads(resp.read().decode('utf-8'))
            no_cot = cot_res["no_cotizacion"]
            print(f" -> No. de Cotización asignado: {no_cot}.")

        # 9. Descargar Cotización PDF
        print("\n[9] Generando y descargando Cotización PDF...")
        with urllib.request.urlopen(f"{url_base}/api/pdf/cotizacion/{sol_id}") as resp:
            pdf_bytes = resp.read()
            assert len(pdf_bytes) > 1000 and pdf_bytes.startswith(b"%PDF"), "Debe ser un PDF valido"
            print(f" -> Cotización PDF generada exitosamente ({len(pdf_bytes):,} bytes).")

        # 10. Pasar a Aceptación y registrar Orden de Compra
        print("\n[10] Registrando Orden de Compra y Aceptación de Partidas...")
        acep_payload = {
            "solicitud_id": sol_id,
            "orden_compra": "OC-2026-MIM-991",
            "fecha_aceptacion": "2026-11-08",
            "partidas_seleccionadas": {str(partida_id): True}
        }
        acep_bytes = json.dumps(acep_payload).encode('utf-8')
        req_acep = urllib.request.Request(f"{url_base}/api/ssi/aceptar-partidas-cliente", data=acep_bytes, headers={'Content-Type': 'application/json'}, method='POST')
        with urllib.request.urlopen(req_acep) as resp:
            assert resp.status == 200
            print(" -> Aceptación registrada. Partida turnada a CS-AT para asignación de fechas.")

        # 11. Programar fechas en CS-AT (regla -2 días recepción)
        print("\n[11] Programando fechas con regla de recepción en CS-AT...")
        prog_payload = {
            "sub_solicitud_id": sub_id,
            "master_id": sol_id,
            "fechas": {
                str(partida_id): {
                    "recepcion": "2026-11-20",
                    "inicio": "2026-11-24",
                    "entrega": "2026-12-01",
                    "limite": "2026-12-01"
                }
            }
        }
        prog_bytes = json.dumps(prog_payload).encode('utf-8')
        req_prog = urllib.request.Request(f"{url_base}/api/at/programar-fechas", data=prog_bytes, headers={'Content-Type': 'application/json'}, method='POST')
        with urllib.request.urlopen(req_prog) as resp:
            assert resp.status == 200
            print(" -> Fechas de calibración registradas y notificadas a SSI.")

        # 12. Descargar Programación PDF y Contrato PDF
        print("\n[12] Generando y descargando Programación y Contrato PDF...")
        with urllib.request.urlopen(f"{url_base}/api/pdf/programacion/{sub_id}") as resp:
            prog_pdf = resp.read()
            assert prog_pdf.startswith(b"%PDF")
            print(f" -> Programación PDF generada ({len(prog_pdf):,} bytes).")

        with urllib.request.urlopen(f"{url_base}/api/pdf/contrato/{sub_id}") as resp:
            contrato_pdf = resp.read()
            assert contrato_pdf.startswith(b"%PDF")
            print(f" -> Contrato Oficial PDF generado ({len(contrato_pdf):,} bytes).")

        # 13. Limpieza a estado cero
        print("\n[13] Ejecutando reinicio seguro a estado cero...")
        req_clean = urllib.request.Request(f"{url_base}/api/mantenimiento/limpiar-bd", data=b"{}", headers={'Content-Type': 'application/json'}, method='POST')
        with urllib.request.urlopen(req_clean) as resp:
            clean_res = json.loads(resp.read().decode('utf-8'))
            assert clean_res["status"] == "success"
            print(" -> Limpieza completada. Base de datos operativa en estado cero (0001-2026PR).")

        print("\n" + "=" * 75)
        print(" ¡TODAS LAS PRUEBAS END-TO-END PASARON CON 100% DE ÉXITO!")
        print(" Servidor ASGI Uvicorn ejecuta y renderiza correctamente sin errores.")
        print("=" * 75)

    finally:
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except Exception:
            proc.kill()
        print("\n[Fin] Servidor Uvicorn cerrado limpiamente.")

if __name__ == "__main__":
    run_e2e_uvicorn_test()
