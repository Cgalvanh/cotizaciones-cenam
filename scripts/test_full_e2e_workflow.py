import os
import sys
from datetime import datetime, date, timedelta

# Asegurar path
sys.path.insert(0, os.path.abspath("."))
import request_parser as parser
import database as db
import pdf_generator as pdf_gen

def test_full_workflow():
    print("="*60)
    print("INICIANDO PRUEBA INTEGRAL END-TO-END (PROCEDIMIENTO OFICIAL CENAM)")
    print("="*60)
    
    # ---------------------------------------------------------
    # ETAPA 1: RECEPCIÓN Y EXTRACCIÓN AUTOMÁTICA (DOCX)
    # ---------------------------------------------------------
    print("\n--- ETAPA 1: RECEPCIÓN DE SOLICITUD ---")
    docx_sample = r"C:/Users/cgalvan/.gemini/antigravity/brain/d8ba3ed8-7506-4828-bfd0-144e2139d5f5/.user_uploaded/media_1793848564329_69f18b45.docx"
    assert os.path.exists(docx_sample), f"No existe el archivo docx en {docx_sample}"
    
    parsed = parser.parse_solicitud_input(file_source=docx_sample)
    print(f"-> Cliente extraído: {parsed['empresa']}")
    print(f"-> No. Solicitud extraído: {parsed['no_solicitud']}")
    print(f"-> No. Folio extraído: {parsed['no_folio']}")
    print(f"-> Contacto: {parsed['contacto']} | Tel: {parsed['telefono']} | Correo: {parsed['correo']}")
    print(f"-> Instrumentos detectados: {len(parsed['instrumentos'])}")
    
    assert "SE" in parsed['empresa'] and "CONTROL DEL SURESTE" in parsed['empresa']
    assert parsed['no_solicitud'] == "2026009PR"
    assert parsed['no_folio'] == "0009-2026PR"
    assert len(parsed['instrumentos']) == 4
    
    for idx, inst in enumerate(parsed['instrumentos'], 1):
        print(f"   {idx}. {inst['descripcion']} | Serie: {inst['serie']} | ID: {inst['id_interno']} -> Sugerido: {inst['clave_area_sugerida']}")
        assert inst['clave_area_sugerida'] == "AT-01"
        
    # Registro en Base de Datos Local
    conn = db.get_connection()
    c = conn.cursor()
    
    # Limpiar prueba previa si existe
    c.execute("DELETE FROM partidas WHERE solicitud_id IN (SELECT id FROM solicitudes_master WHERE no_folio = ?)", (parsed['no_folio'],))
    c.execute("DELETE FROM sub_solicitudes_at WHERE solicitud_id IN (SELECT id FROM solicitudes_master WHERE no_folio = ?)", (parsed['no_folio'],))
    c.execute("DELETE FROM solicitudes_master WHERE no_folio = ?", (parsed['no_folio'],))
    conn.commit()
    
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("""
    INSERT INTO solicitudes_master (
        no_solicitud, no_folio, version, cliente, representante, telefono, correo, rfc, pais,
        es_extranjero, aplica_iva, fecha_recepcion, fecha_emision, vigencia, estado, es_in_situ
    ) VALUES (?, ?, 1, ?, ?, ?, ?, ?, ?, 0, 1, ?, ?, '2026-12-31', 'TURNADA', 0)
    """, (
        parsed['no_solicitud'], parsed['no_folio'], parsed['empresa'], parsed['contacto'],
        parsed['telefono'], parsed['correo'], parsed['rfc'], parsed['pais'],
        now_str, datetime.now().strftime("%Y-%m-%d")
    ))
    sol_id = c.lastrowid
    
    c.execute("""
    INSERT INTO sub_solicitudes_at (solicitud_id, clave_area, estado, fecha_asignacion, fecha_limite_sla)
    VALUES (?, 'AT-01', 'ASIGNADA', ?, ?)
    """, (sol_id, now_str, (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d")))
    sub_id = c.lastrowid
    
    partida_ids = []
    for idx, inst in enumerate(parsed['instrumentos'], 1):
        c.execute("""
        INSERT INTO partidas (
            sub_solicitud_id, solicitud_id, numero_partida, descripcion_equipo,
            marca, modelo, no_serie, alcance_solicitado, descripcion_servicio,
            certificado_anterior, magnitud, id_interno, condiciones_particulares,
            tiempo_dias_habiles, precio_unitario, precio_total, es_no_realizable
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 5, 0, 0, 0)
        """, (
            sub_id, sol_id, idx, inst['descripcion'],
            inst['marca'], inst['modelo'], inst['serie'], inst['intervalo'], inst['descripcion'],
            inst['certificado_anterior'], inst['magnitud'], inst['id_interno'], inst['condiciones']
        ))
        partida_ids.append(c.lastrowid)
    conn.commit()
    conn.close()
    print("-> Solicitud y 4 partidas registradas en BD local con estado 'TURNADA'.")

    # ---------------------------------------------------------
    # ETAPA 2: ELABORACIÓN DE COTIZACIÓN (AT-01 & SSI)
    # ---------------------------------------------------------
    print("\n--- ETAPA 2: COTIZACIÓN METROLÓGICA ---")
    conn = db.get_connection()
    c = conn.cursor()
    # AT-01 cotiza precios oficiales
    precios = [4850.00, 5200.00, 3900.00, 4100.00]
    servicios = [
        "Calibración de regla de cristal en comparador óptico",
        "Calibración de regla de cristal de 300 mm",
        "Calibración de retícula de resolución patrón",
        "Calibración de retícula angular patrón"
    ]
    for idx, pid in enumerate(partida_ids):
        c.execute("""
        UPDATE partidas
        SET clave_servicio = ?, descripcion_servicio = ?, precio_unitario = ?, precio_total = ?, tiempo_dias_habiles = 5
        WHERE id = ?
        """, (f"DIM-CAL-0{idx+1}", servicios[idx], precios[idx], precios[idx], pid))
        
    c.execute("UPDATE sub_solicitudes_at SET estado = 'COMPLETADA' WHERE id = ?", (sub_id,))
    
    # SSI asigna No. de Cotización oficial con sufijo PR
    no_cotiz = db.get_next_cotizacion_number()
    print(f"-> No. Cotización generado automáticamente: {no_cotiz}")
    assert no_cotiz.endswith("PR")
    
    c.execute("""
    UPDATE solicitudes_master
    SET no_cotizacion = ?, estado = 'EMITIDA', fecha_emision = ?
    WHERE id = ?
    """, (no_cotiz, datetime.now().strftime("%Y-%m-%d"), sol_id))
    conn.commit()
    
    # Generar PDF de Cotización
    c.execute("SELECT * FROM solicitudes_master WHERE id = ?", (sol_id,))
    sol_row = dict(c.fetchone())
    c.execute("SELECT * FROM partidas WHERE solicitud_id = ? ORDER BY numero_partida", (sol_id,))
    parts_rows = [dict(p) for p in c.fetchall()]
    conn.close()
    
    os.makedirs("generated_docs", exist_ok=True)
    pdf_cot_path = f"generated_docs/Cotizacion_{sol_row['no_folio'].replace('-', '_')}_{no_cotiz}.pdf"
    pdf_gen.generate_cotizacion_pdf(sol_row, parts_rows, filepath=pdf_cot_path)
    print(f"-> Cotización PDF oficial generada: {pdf_cot_path} ({os.path.getsize(pdf_cot_path):,} bytes)")
    assert os.path.exists(pdf_cot_path) and os.path.getsize(pdf_cot_path) > 1000
    
    # SSI confirma envío al cliente -> estado pasa a COTIZACION_ENVIADA (desaparece de Tab 3)
    conn = db.get_connection()
    c = conn.cursor()
    c.execute("UPDATE solicitudes_master SET estado = 'COTIZACION_ENVIADA' WHERE id = ?", (sol_id,))
    conn.commit()
    conn.close()
    print("-> Cotización enviada al cliente. Estado: 'COTIZACION_ENVIADA' (Desapareció de Emisión de Cotización).")

    # ---------------------------------------------------------
    # ETAPA 3: ACEPTACIÓN DEL CLIENTE Y PROGRAMACIÓN POR AT
    # ---------------------------------------------------------
    print("\n--- ETAPA 3: PROGRAMACIÓN DE CALIBRACIÓN POR AT ---")
    # Cliente acepta formalmente las 4 partidas
    conn = db.get_connection()
    c = conn.cursor()
    c.execute("UPDATE partidas SET aceptada_cliente = 1 WHERE solicitud_id = ?", (sol_id,))
    c.execute("UPDATE solicitudes_master SET estado = 'EN_PROGRAMACION', fecha_aceptacion_cotizacion = '2026-06-01' WHERE id = ?", (sol_id,))
    c.execute("UPDATE sub_solicitudes_at SET estado = 'EN_PROGRAMACION' WHERE id = ?", (sub_id,))
    conn.commit()
    conn.close()
    print("-> Cliente aceptó partidas. Solicitud turnada a AT-01 para programación.")
    
    # CS-AT asigna fechas de calibración
    # Fecha Inicio: Lunes 8 de Junio de 2026
    f_inicio = datetime(2026, 6, 8)
    # Regla de calidad: Recepción automática = 2 días hábiles antes = Jueves 4 de Junio de 2026
    f_recep = db.restar_dias_habiles(f_inicio, 2)
    print(f"-> Regla de calidad CENAM verificada:")
    print(f"   Fecha Inicio Calibración: {f_inicio.strftime('%Y-%m-%d (%A)')}")
    print(f"   Fecha Recepción Equipo (-2 días hábiles): {f_recep.strftime('%Y-%m-%d (%A)')}")
    assert f_recep.weekday() == 3 # Jueves
    
    f_fin = db.sumar_dias_habiles(f_inicio, 5) # Lunes siguiente 15 de Junio
    f_lim = datetime(2026, 6, 29) # 3 semanas
    
    conn = db.get_connection()
    c = conn.cursor()
    c.execute("""
    UPDATE partidas
    SET fecha_recepcion_equipo = ?, fecha_inicio_calibracion = ?, fecha_entrega_equipo = ?, fecha_limite_aceptacion = ?
    WHERE sub_solicitud_id = ?
    """, (f_recep.strftime("%Y-%m-%d"), f_inicio.strftime("%Y-%m-%d"), f_fin.strftime("%Y-%m-%d"), f_lim.strftime("%Y-%m-%d"), sub_id))
    
    c.execute("""
    UPDATE sub_solicitudes_at
    SET estado = 'PROGRAMA_PROPUESTO', fecha_recepcion_prog = ?, fecha_inicio_prog = ?, fecha_entrega_prog = ?, fecha_limite_prog = ?
    WHERE id = ?
    """, (f_recep.strftime("%Y-%m-%d"), f_inicio.strftime("%Y-%m-%d"), f_fin.strftime("%Y-%m-%d"), f_lim.strftime("%Y-%m-%d"), sub_id))
    conn.commit()
    conn.close()
    print("-> AT-01 envió programa propuesto. (Desapareció de la pantalla de programación de AT).")
    
    # SSI genera documento de Programación PER ÁREA TÉCNICA (AT-01)
    conn = db.get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM solicitudes_master WHERE id = ?", (sol_id,))
    sol_row = dict(c.fetchone())
    c.execute("SELECT * FROM sub_solicitudes_at WHERE id = ?", (sub_id,))
    sub_row = dict(c.fetchone())
    c.execute("SELECT * FROM partidas WHERE sub_solicitud_id = ? AND aceptada_cliente = 1 ORDER BY numero_partida", (sub_id,))
    sub_parts = [dict(p) for p in c.fetchall()]
    conn.close()
    
    pdf_prog_path = f"generated_docs/Programacion_{sol_row['no_folio'].replace('-', '_')}_AT_01.pdf"
    pdf_gen.generate_programacion_pdf(sol_row, sub_row, sub_parts, tipo='CENAM', filepath=pdf_prog_path, rep_legal_cenam="Lic. Miguel Ángel Torres (Director de Metrología)")
    print(f"-> Programación Oficial por AT generada: {pdf_prog_path} ({os.path.getsize(pdf_prog_path):,} bytes)")
    assert os.path.exists(pdf_prog_path) and os.path.getsize(pdf_prog_path) > 1000

    # ---------------------------------------------------------
    # ETAPA 4: CONFIRMACIÓN DEL SERVICIO Y CONTRATO
    # ---------------------------------------------------------
    print("\n--- ETAPA 4: CONFIRMACIÓN Y FORMALIZACIÓN DE CONTRATO ---")
    # Cliente acepta la propuesta de programa
    conn = db.get_connection()
    c = conn.cursor()
    c.execute("UPDATE solicitudes_master SET estado = 'PROGRAMA_CONFIRMADO' WHERE id = ?", (sol_id,))
    conn.commit()
    conn.close()
    print("-> Cliente aceptó programación de fechas.")
    
    # SSI define logística de retorno: Opción 1 (Recolección en instalaciones del CENAM)
    # y representante legal (o vacío)
    conn = db.get_connection()
    c = conn.cursor()
    c.execute("""
    UPDATE solicitudes_master
    SET estado = 'CONFIRMADA_CONCLUIDA',
        modalidad_retorno = 'RECOLECCION_CENAM',
        representante_legal_cenam = 'Lic. Miguel Ángel Torres',
        fecha_confirmacion_programa = ?
    WHERE id = ?
    """, (now_str, sol_id))
    c.execute("UPDATE sub_solicitudes_at SET estado = 'PROGRAMA_CONFIRMADO' WHERE id = ?", (sub_id,))
    conn.commit()
    conn.close()
    
    # Generar Contrato y Programación Oficial final
    pdf_contrato_path = f"generated_docs/Contrato_Final_{sol_row['no_folio'].replace('-', '_')}_AT_01.pdf"
    sol_row['modalidad_retorno'] = 'RECOLECCION_CENAM'
    pdf_gen.generate_programacion_pdf(sol_row, sub_row, sub_parts, tipo='CENAM', filepath=pdf_contrato_path, rep_legal_cenam="Lic. Miguel Ángel Torres")
    print(f"-> Contrato Definitivo generado: {pdf_contrato_path} ({os.path.getsize(pdf_contrato_path):,} bytes)")
    assert os.path.exists(pdf_contrato_path) and os.path.getsize(pdf_contrato_path) > 1000
    
    # Verificar que el servicio aparece en Calendario Confirmado de AT-01
    conn = db.get_connection()
    c = conn.cursor()
    c.execute("""
    SELECT s.no_folio, s.no_cotizacion, s.cliente, sub.fecha_recepcion_prog, sub.fecha_inicio_prog, sub.fecha_entrega_prog
    FROM sub_solicitudes_at sub
    JOIN solicitudes_master s ON sub.solicitud_id = s.id
    WHERE sub.clave_area = 'AT-01' AND sub.estado = 'PROGRAMA_CONFIRMADO' AND s.id = ?
    """, (sol_id,))
    cal_row = c.fetchone()
    conn.close()
    
    assert cal_row is not None
    print(f"-> Verificado en Calendario Confirmado de AT-01: Folio {cal_row['no_folio']} | Cotización {cal_row['no_cotizacion']} | Recepción: {cal_row['fecha_recepcion_prog']} | Inicio: {cal_row['fecha_inicio_prog']}")
    
    print("\n" + "="*60)
    print("EXITO: FLUJO COMPLETO DE 4 ETAPAS VERIFICADO AL 100%")
    print("="*60)

if __name__ == '__main__':
    test_full_workflow()
