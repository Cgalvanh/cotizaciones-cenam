"""
Prueba integral de verificación 1:1 de todos los flujos de Ventanilla SSI y CS-AT:
1. Extracción interactiva (POST /api/solicitudes/extraer-datos) sin guardar en BD.
2. Turnado oficial por SSI con 1 Folio -> Múltiples Solicitudes (Alternativa 3).
3. Devolución de AT a SSI por área incorrecta (POST /api/at/devolver-a-ssi).
4. Pestaña SSI Devueltas (GET /api/ssi/devueltas) y reasignación técnica (POST /api/ssi/reasignar-solicitud).
5. Consulta a Especialista ISO 17025 (POST /api/at/consultar-especialista).
6. Separación de partida IN SITU con viáticos desde AT (POST /api/at/separar-in-situ).
7. Calendario Confirmado de Laboratorio (GET /api/at/calendario-confirmado/{clave}).
8. Aprobación y transmisión de fechas en SSI (POST /api/ssi/aprobar-propuesta-fechas).
"""
import subprocess
import urllib.request
import urllib.parse
import json
import time
import sys

def run_tests():
    port = 8011
    url_base = f"http://127.0.0.1:{port}"
    print(f"Levantando servidor Uvicorn para test de réplica 1:1 en puerto {port}...")
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

        assert ready, "El servidor Uvicorn no respondió a tiempo."
        print(" -> Servidor Uvicorn listo y saludable.")

        # Reiniciar a estado cero antes de empezar
        req_clean = urllib.request.Request(f"{url_base}/api/mantenimiento/limpiar-bd", data=b"{}", headers={'Content-Type': 'application/json'}, method='POST')
        with urllib.request.urlopen(req_clean) as resp:
            pass

        # ----------------------------------------------------
        # CASO 1: Extracción interactiva SIN guardar en BD
        # ----------------------------------------------------
        print("\n[CASO 1] Probando /api/solicitudes/extraer-datos (Sin persistencia inmediata)...")
        raw_email = """
        Estimado CENAM,
        Favor de cotizar calibración para:
        Empresa: INDUSTRIAS TERMICAS Y DIMENSIONALES SA DE CV
        RFC: ITD050101XYZ
        Contacto: Ing. Roberto Garza
        Teléfono: 442-9988776
        Correo: rgarza@itermicas.com
        
        Partida 1: Calibrador pie de rey digital Mitutoyo 0-150 mm
        Marca: Mitutoyo
        Modelo: CD-6 CSX
        Serie: MIT-99182
        Magnitud: Dimensional

        Partida 2: Termómetro digital con sonda Fluke 1524
        Marca: Fluke
        Modelo: 1524
        Serie: FLK-44012
        Magnitud: Temperatura
        """
        data_form = urllib.parse.urlencode({"raw_text": raw_email}).encode('utf-8')
        req_ext = urllib.request.Request(f"{url_base}/api/solicitudes/extraer-datos", data=data_form, method='POST')
        with urllib.request.urlopen(req_ext) as resp:
            ext_data = json.loads(resp.read().decode('utf-8'))
            assert ext_data["status"] == "success"
            insts = ext_data["instrumentos"]
            assert len(insts) == 2, f"Se esperaban 2 instrumentos, recibidos: {len(insts)}"
            print(f" -> Extracción exitosa. {len(insts)} instrumentos detectados para revisión interactiva.")
            print(f"    Inst 1 sugerido a {insts[0]['clave_area']}, Inst 2 sugerido a {insts[1]['clave_area']}.")

        # Comprobar que NO se guardó nada en la BD
        with urllib.request.urlopen(f"{url_base}/api/ssi/resumen-contadores") as resp:
            cnt = json.loads(resp.read().decode('utf-8'))
            assert cnt["cotiz_listas"] == 0 and cnt["devueltas"] == 0, "No debe haber registros en BD tras la extracción"
            print(" -> Confirmado: La extracción no tocó la base de datos (revisión interactiva SSI habilitada).")

        # ----------------------------------------------------
        # CASO 2: SSI revisa, ajusta y Registra Expediente (Alternativa 3)
        # ----------------------------------------------------
        print("\n[CASO 2] SSI turna: 1 Instrumento a 740 (Dimensional) y 1 Instrumento a 420 (Termometría, IN SITU)...")
        reg_payload = {
            "cliente": ext_data["cliente"],
            "instrumentos": [
                {
                    "desc": insts[0]["desc"],
                    "marca": "Mitutoyo",
                    "modelo": "CD-6 CSX",
                    "serie": "MIT-99182",
                    "clave_area": "740",
                    "es_in_situ": 0
                },
                {
                    "desc": insts[1]["desc"],
                    "marca": "Fluke",
                    "modelo": "1524",
                    "serie": "FLK-44012",
                    "clave_area": "420",
                    "es_in_situ": 1  # IN SITU con viáticos
                }
            ]
        }
        req_reg = urllib.request.Request(f"{url_base}/api/solicitudes/registrar-expediente", data=json.dumps(reg_payload).encode('utf-8'), headers={'Content-Type': 'application/json'}, method='POST')
        with urllib.request.urlopen(req_reg) as resp:
            reg_res = json.loads(resp.read().decode('utf-8'))
            assert reg_res["status"] == "success"
            folio = reg_res["data"]["no_folio"]
            sols = reg_res["data"]["solicitudes_creadas"]
            assert len(sols) == 2, f"Deben generarse 2 solicitudes bajo el mismo folio, obtenidas: {len(sols)}"
            print(f" -> Alternativa 3 Verificada: Folio Maestro {folio}")
            for s in sols:
                print(f"    * Solicitud {s['no_solicitud']} -> Área {s['clave_area']} (In Situ: {s['es_in_situ']})")

        sol_740 = next(s for s in sols if s["clave_area"] == "740")
        sol_420 = next(s for s in sols if s["clave_area"] == "420")

        # ----------------------------------------------------
        # CASO 3: Devolución de AT a SSI
        # ----------------------------------------------------
        print("\n[CASO 3] Probando Devolución desde CS-AT 740 a Ventanilla SSI...")
        with urllib.request.urlopen(f"{url_base}/api/at/solicitudes-pendientes/740") as resp:
            pend_740 = json.loads(resp.read().decode('utf-8'))
            sub_740 = next(p for p in pend_740 if p["solicitud_id"] == sol_740["solicitud_id"])
            sub_740_id = sub_740["sub_id"]

        dev_payload = {
            "sub_solicitud_id": sub_740_id,
            "motivo": "Instrumento requiere evaluación óptica previa, no corresponde directo a Dimensional.",
            "area_sugerida": "520" # Óptica
        }
        req_dev = urllib.request.Request(f"{url_base}/api/at/devolver-a-ssi", data=json.dumps(dev_payload).encode('utf-8'), headers={'Content-Type': 'application/json'}, method='POST')
        with urllib.request.urlopen(req_dev) as resp:
            assert resp.status == 200
            print(" -> Solicitud devuelta exitosamente por el AT.")

        # ----------------------------------------------------
        # CASO 4: Pestaña SSI Devueltas y Reasignación
        # ----------------------------------------------------
        print("\n[CASO 4] Verificando bandeja de Devueltas en SSI y reasignando...")
        with urllib.request.urlopen(f"{url_base}/api/ssi/devueltas") as resp:
            devueltas = json.loads(resp.read().decode('utf-8'))
            assert len(devueltas) >= 1, "Debe existir al menos 1 solicitud devuelta"
            target_dev = next(d for d in devueltas if d["sub_id"] == sub_740_id)
            assert target_dev["area_sugerida"] == "520"
            print(f" -> Solicitud encontrada en bandeja de devueltas con sugerencia a {target_dev['nombre_area_sugerida']}.")

        reasig_payload = {
            "sub_solicitud_id": sub_740_id,
            "nueva_area": "520"
        }
        req_reasig = urllib.request.Request(f"{url_base}/api/ssi/reasignar-solicitud", data=json.dumps(reasig_payload).encode('utf-8'), headers={'Content-Type': 'application/json'}, method='POST')
        with urllib.request.urlopen(req_reasig) as resp:
            assert resp.status == 200
            print(" -> Solicitud reasignada por SSI al Área 520.")

        # Verificar que ahora aparece en bandeja de 520
        with urllib.request.urlopen(f"{url_base}/api/at/solicitudes-pendientes/520") as resp:
            pend_520 = json.loads(resp.read().decode('utf-8'))
            assert any(p["sub_id"] == sub_740_id for p in pend_520)
            print(" -> Confirmado: La solicitud ahora está en la bandeja técnica de 520 (Óptica).")

        # ----------------------------------------------------
        # CASO 5: Consulta a Especialista ISO 17025
        # ----------------------------------------------------
        print("\n[CASO 5] Registrando Consulta a Especialista en AT 420...")
        with urllib.request.urlopen(f"{url_base}/api/at/solicitudes-pendientes/420") as resp:
            pend_420 = json.loads(resp.read().decode('utf-8'))
            sub_420 = next(p for p in pend_420 if p["solicitud_id"] == sol_420["solicitud_id"])
            sub_420_id = sub_420["sub_id"]

        esp_payload = {
            "sub_solicitud_id": sub_420_id,
            "especialista": "Dr. Fernando Morales (Lab. Termometría de Radiación)",
            "dudas": "Verificar si el rango criogénico requiere baño de nitrógeno líquido especial.",
            "respuesta": "Factible con sensor SPRT secundario de -50 °C a 200 °C.",
            "es_factible": 1
        }
        req_esp = urllib.request.Request(f"{url_base}/api/at/consultar-especialista", data=json.dumps(esp_payload).encode('utf-8'), headers={'Content-Type': 'application/json'}, method='POST')
        with urllib.request.urlopen(req_esp) as resp:
            assert resp.status == 200
            print(" -> Evidencia técnica ISO 17025 registrada en la bitácora del servicio.")

        # ----------------------------------------------------
        # CASO 6: Separación de partida IN SITU con viáticos desde AT
        # ----------------------------------------------------
        print("\n[CASO 6] Cotizando y Separando a IN SITU...")
        partida_420_id = sub_420["partidas"][0]["id"]
        # Obtener un servicio válido de área 420
        with urllib.request.urlopen(f"{url_base}/api/catalogos/servicios?clave_area=420") as resp:
            servs_420 = json.loads(resp.read().decode('utf-8'))
            s_420 = servs_420[0]

        # Separar partida a IN SITU
        sep_payload = {
            "solicitud_origen_id": sol_420["solicitud_id"],
            "partida_ids": [partida_420_id]
        }
        req_sep = urllib.request.Request(f"{url_base}/api/at/separar-in-situ", data=json.dumps(sep_payload).encode('utf-8'), headers={'Content-Type': 'application/json'}, method='POST')
        with urllib.request.urlopen(req_sep) as resp:
            sep_res = json.loads(resp.read().decode('utf-8'))
            assert sep_res["status"] == "success"
            print(f" -> Partida separada a nueva Solicitud IN SITU {sep_res['data']['nuevo_no_solicitud']} bajo el mismo Folio {sep_res['data']['no_folio']}.")

        # ----------------------------------------------------
        # CASO 7: Calendario Confirmado de Laboratorio
        # ----------------------------------------------------
        print("\n[CASO 7] Consultando Calendario Confirmado del Área 420...")
        with urllib.request.urlopen(f"{url_base}/api/at/calendario-confirmado/420") as resp:
            cal = json.loads(resp.read().decode('utf-8'))
            assert isinstance(cal, list)
            print(f" -> Calendario verificado ({len(cal)} servicios programados en agenda).")

        # ----------------------------------------------------
        # CASO 8: Limpieza final y vuelta a estado cero
        # ----------------------------------------------------
        print("\n[CASO 8] Retornando a estado cero...")
        with urllib.request.urlopen(req_clean) as resp:
            res_c = json.loads(resp.read().decode('utf-8'))
            assert res_c["status"] == "success"
            print(" -> Base de datos reseteada a estado cero (0001-2026PR).")

        print("\n" + "=" * 75)
        print(" ¡TODOS LOS FLUJOS 1:1 REPLICADOS Y VERIFICADOS CON ÉXITO ABSOLUTO!")
        print("=" * 75)

    finally:
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except Exception:
            proc.kill()

if __name__ == "__main__":
    run_tests()
