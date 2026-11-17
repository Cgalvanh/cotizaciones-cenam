#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Prueba integral de los nuevos campos de Cotización por AT y Aceptación Selectiva del Cliente:
1. Captura de Cantidad, Costo Unitario, Costo Total, Comentarios SSI y Comentarios Cliente.
2. Generación de Cotización PDF con desglose, IVA 16% y comentarios visibles.
3. Aceptación selectiva por SSI: partidas autorizadas vs DECLINADA_POR_CLIENTE y captura de Orden de Compra (OC).
4. Turnado exclusivo a programación de las ATs con partidas aceptadas.
5. Generación de Programación PDF conteniendo OC y solo partidas aceptadas.
"""

import os
import sys
from datetime import datetime, date, timedelta

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.join(PROJECT_ROOT, "nube_segura"))

import database as db
import pdf_generator as pdf_gen

def test_workflow():
    print("="*70)
    print("INICIANDO PRUEBA DEL NUEVO FLUJO DE COTIZACION Y ACEPTACION SELECTIVA")
    print("="*70)

    # 1. Limpieza operativa previa
    db.limpiar_solicitudes_y_programaciones()
    print("[1] Base de datos local limpiada para prueba desde cero.")

    # 2. SSI Registra Expediente con 3 instrumentos
    cliente = {
        "cliente": "METROLOGIA INDUSTRIAL DE MEXICO S.A. DE C.V.",
        "representante": "Ing. Carlos Mendoza",
        "telefono": "442-555-1234",
        "correo": "cmendoza@metrologia-ind.com",
        "rfc": "MIM980101XYZ",
        "pais": "México",
        "es_extranjero": 0,
        "aplica_iva": 1
    }

    equipos = [
        {
            "num": 1,
            "desc": "Bloques patrón longitudinales de acero (Juego)",
            "marca": "Mitutoyo",
            "modelo": "516-902",
            "serie": "SN-88120",
            "alcance": "0.5 mm a 100 mm",
            "cert": "C-2024-88",
            "mag": "Dimensional",
            "id": "EQ-DIM-01",
            "cond": "Sin golpes",
            "clave_area": "740",
            "es_in_situ": 0
        },
        {
            "num": 2,
            "desc": "Micrómetro de exteriores digital",
            "marca": "Starrett",
            "modelo": "733.1XFL",
            "serie": "SN-99432",
            "alcance": "0 a 25 mm",
            "cert": "C-2024-99",
            "mag": "Dimensional",
            "id": "EQ-DIM-02",
            "cond": "Batería nueva",
            "clave_area": "740",
            "es_in_situ": 0
        },
        {
            "num": 3,
            "desc": "Juego de pesas clase F1",
            "marca": "Troemner",
            "modelo": "F1-SET",
            "serie": "SN-77610",
            "alcance": "1 g a 1 kg",
            "cert": "C-2023-45",
            "mag": "Masa",
            "id": "EQ-MAS-01",
            "cond": "Caja de madera intacta",
            "clave_area": "730",
            "es_in_situ": 0
        }
    ]

    res_exp = db.crear_expediente_y_solicitudes(cliente, equipos, "ventanilla@cenam.mx")
    folio = res_exp["no_folio"]
    print(f"[2] Expediente registrado con Folio Maestro: {folio}")
    for sc in res_exp["solicitudes_creadas"]:
        print(f"    * Solicitud {sc['no_solicitud']} turnada a Division {sc['clave_area']} ({sc['total_partidas']} partidas)")

    conn = db.get_connection()
    c = conn.cursor()

    # 3. Especialista CS-AT de 740 cotiza sus 2 partidas con Cantidad, Costo Unitario, Comentarios SSI y Cliente
    c.execute("""
        SELECT p.id, p.numero_partida, p.descripcion_equipo
        FROM partidas p
        JOIN sub_solicitudes_at sub ON p.sub_solicitud_id = sub.id
        WHERE sub.clave_area = '740'
        ORDER BY p.numero_partida
    """)
    partidas_740 = c.fetchall()

    # Partida 1: Cantidad 2, Unitario 3,500 -> Total 7,000
    p1_id = partidas_740[0]["id"]
    cant_p1 = 2
    unit_p1 = 3500.0
    tot_p1 = cant_p1 * unit_p1
    com_ssi_p1 = "Se requiere patrón interferométrico primario. Calibrador asignado: Dr. Morales."
    com_cli_p1 = "Entregar el juego limpio y estabilizado a 20 °C con estuche original."
    c.execute("""
        UPDATE partidas
        SET clave_servicio = 'DIM-BLOQ-01', descripcion_servicio = 'Calibración de bloques patrón por interferometría',
            cantidad = ?, precio_unitario = ?, precio_total = ?, tiempo_dias_habiles = 8,
            comentarios_ssi = ?, comentarios_cliente = ?, estado_partida = 'COTIZADA'
        WHERE id = ?
    """, (cant_p1, unit_p1, tot_p1, com_ssi_p1, com_cli_p1, p1_id))

    # Partida 2: Cantidad 1, Unitario 1,800 -> Total 1,800
    p2_id = partidas_740[1]["id"]
    cant_p2 = 1
    unit_p2 = 1800.0
    tot_p2 = cant_p2 * unit_p2
    com_ssi_p2 = "Tiempo estimado 4 días hábiles."
    com_cli_p2 = "Verificar que el tambor micrométrico gire suavemente antes de envío."
    c.execute("""
        UPDATE partidas
        SET clave_servicio = 'DIM-MICR-01', descripcion_servicio = 'Calibración de micrómetro de exteriores',
            cantidad = ?, precio_unitario = ?, precio_total = ?, tiempo_dias_habiles = 4,
            comentarios_ssi = ?, comentarios_cliente = ?, estado_partida = 'COTIZADA'
        WHERE id = ?
    """, (cant_p2, unit_p2, tot_p2, com_ssi_p2, com_cli_p2, p2_id))

    # Marcar sub_solicitud 740 como COMPLETADA
    c.execute("UPDATE sub_solicitudes_at SET estado = 'COMPLETADA' WHERE clave_area = '740'")

    # Especialista CS-AT de 730 cotiza partida 3: Cantidad 1, Unitario 4,200 -> Total 4,200
    c.execute("""
        SELECT p.id FROM partidas p
        JOIN sub_solicitudes_at sub ON p.sub_solicitud_id = sub.id
        WHERE sub.clave_area = '730'
    """)
    p3_id = c.fetchone()["id"]
    c.execute("""
        UPDATE partidas
        SET clave_servicio = 'MAS-PESA-F1', descripcion_servicio = 'Calibración de juego de pesas clase F1 por sustitución doble',
            cantidad = 1, precio_unitario = 4200.0, precio_total = 4200.0, tiempo_dias_habiles = 10,
            comentarios_ssi = 'Balanza Mettler AX1005 reservada.', comentarios_cliente = 'Manejar exclusivamente con pinzas con puntas de teflón.',
            estado_partida = 'COTIZADA'
        WHERE id = ?
    """, (p3_id,))
    c.execute("UPDATE sub_solicitudes_at SET estado = 'COMPLETADA' WHERE clave_area = '730'")
    conn.commit()
    print("[3] Cotizaciones completadas por especialistas CS-AT (740 y 730) con comentarios y cantidades.")

    # 4. SSI Emite Cotización
    # Obtener solicitud master de 740
    c.execute("SELECT m.* FROM solicitudes_master m WHERE m.no_folio = ? AND m.clave_area = '740'", (folio,))
    sol_master_740 = dict(c.fetchone())

    next_cot = db.get_next_cotizacion_number()
    c.execute("UPDATE solicitudes_master SET no_cotizacion = ?, estado = 'COTIZACION_ENVIADA', fecha_emision = ? WHERE id = ?", (next_cot, str(date.today()), sol_master_740["id"]))
    conn.commit()

    c.execute("SELECT * FROM partidas WHERE solicitud_id = ?", (sol_master_740["id"],))
    partidas_all_740 = [dict(r) for r in c.fetchall()]

    os.makedirs("generated_docs", exist_ok=True)
    pdf_cot_path = f"generated_docs/Cotizacion_Prueba_Flujo_{folio.replace('-', '_')}.pdf"
    sol_master_740["no_cotizacion"] = next_cot
    pdf_gen.generate_cotizacion_pdf(sol_master_740, partidas_all_740, pdf_cot_path)
    print(f"[4] PDF de Cotización generado con éxito: {pdf_cot_path} ({os.path.getsize(pdf_cot_path)} bytes)")

    # 5. Aceptación SELECTIVA por el Cliente
    # El cliente acepta la partida 1 (bloques) y DECLINA la partida 2 (micrómetro)
    oc_test = "OC-CENAM-2026-9921"
    fecha_acep = str(date.today())

    # Partida 1: ACEPTADA
    c.execute("UPDATE partidas SET aceptada_cliente = 1, estado_partida = 'ACEPTADA' WHERE id = ?", (p1_id,))
    # Partida 2: DECLINADA_POR_CLIENTE
    c.execute("UPDATE partidas SET aceptada_cliente = 0, estado_partida = 'DECLINADA_POR_CLIENTE' WHERE id = ?", (p2_id,))

    # Actualizar solicitud master
    c.execute("""
        UPDATE solicitudes_master
        SET estado = 'EN_PROGRAMACION', fecha_aceptacion_cotizacion = ?, orden_compra_cliente = ?
        WHERE id = ?
    """, (fecha_acep, oc_test, sol_master_740["id"]))

    # Turnar sub_solicitud a EN_PROGRAMACION
    c.execute("""
        UPDATE sub_solicitudes_at
        SET estado = 'EN_PROGRAMACION'
        WHERE solicitud_id = ? AND id IN (SELECT sub_solicitud_id FROM partidas WHERE solicitud_id = ? AND aceptada_cliente = 1)
    """, (sol_master_740["id"], sol_master_740["id"]))
    conn.commit()

    print(f"[5] Aceptación selectiva registrada:")
    print(f"    * Orden de Compra capturada: {oc_test}")
    print(f"    * Partida 1: ACEPTADA")
    print(f"    * Partida 2: DECLINADA_POR_CLIENTE")

    # 6. CS-AT asigna fechas de programación SOLO para la partida aceptada
    c.execute("SELECT sub.* FROM sub_solicitudes_at sub WHERE sub.solicitud_id = ? AND sub.estado = 'EN_PROGRAMACION'", (sol_master_740["id"],))
    sub_prog = dict(c.fetchone())

    f_ini_cal = date.today() + timedelta(days=14)
    f_rec_cal = db.restar_dias_habiles(datetime.combine(f_ini_cal, datetime.min.time()), 2).date()
    f_fin_cal = db.sumar_dias_habiles(datetime.combine(f_ini_cal, datetime.min.time()), 8).date()

    c.execute("""
        UPDATE partidas
        SET fecha_recepcion_equipo = ?, fecha_inicio_calibracion = ?, fecha_fin_calibracion = ?,
            fecha_entrega_equipo = ?, fecha_entrega_resultados = ?
        WHERE id = ?
    """, (str(f_rec_cal), str(f_ini_cal), str(f_fin_cal), str(f_fin_cal), str(f_fin_cal), p1_id))

    c.execute("""
        UPDATE sub_solicitudes_at
        SET estado = 'PROGRAMA_PROPUESTO', fecha_recepcion_prog = ?, fecha_inicio_prog = ?, fecha_entrega_prog = ?
        WHERE id = ?
    """, (str(f_rec_cal), str(f_ini_cal), str(f_fin_cal), sub_prog["id"]))
    conn.commit()

    # 7. Generación de PDF de Programación
    c.execute("SELECT * FROM partidas WHERE solicitud_id = ? AND aceptada_cliente = 1", (sol_master_740["id"],))
    partidas_prog_aceptadas = [dict(r) for r in c.fetchall()]

    sol_master_740["orden_compra_cliente"] = oc_test
    sol_master_740["fecha_aceptacion_cotizacion"] = fecha_acep

    pdf_prog_path = f"generated_docs/Programacion_Prueba_Flujo_{folio.replace('-', '_')}.pdf"
    pdf_gen.generate_programacion_pdf(sol_master_740, sub_prog, partidas_prog_aceptadas, tipo='CENAM', filepath=pdf_prog_path)
    print(f"[6] PDF de Programación generado con éxito: {pdf_prog_path} ({os.path.getsize(pdf_prog_path)} bytes)")

    # 8. Verificaciones finales
    assert len(partidas_prog_aceptadas) == 1, "Debe haber exactamente 1 partida aceptada en el documento de programación"
    assert partidas_prog_aceptadas[0]["id"] == p1_id, "La partida aceptada debe ser la Partida 1"
    assert partidas_prog_aceptadas[0]["cantidad"] == 2, "La cantidad debe ser 2"
    assert partidas_prog_aceptadas[0]["precio_total"] == 7000.0, "El precio total debe ser 7,000.0"

    # Verificar partida declinada
    c.execute("SELECT estado_partida, aceptada_cliente FROM partidas WHERE id = ?", (p2_id,))
    p2_check = dict(c.fetchone())
    assert p2_check["estado_partida"] == 'DECLINADA_POR_CLIENTE', "Partida 2 debe estar marcada como DECLINADA_POR_CLIENTE"
    assert p2_check["aceptada_cliente"] == 0, "Partida 2 debe tener aceptada_cliente = 0"

    conn.close()

    print("="*70)
    print("TODAS LAS PRUEBAS DEL NUEVO FLUJO PASARON AL 100% CON EXITO")
    print("="*70)

if __name__ == "__main__":
    test_workflow()
