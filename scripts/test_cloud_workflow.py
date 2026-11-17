import os
import sys
from datetime import datetime, date, timedelta

# Configurar path para nube_segura
sys.path.insert(0, os.path.abspath("nube_segura"))
import request_parser as parser
import cloud_db as cdb
import pdf_generator as pdf_gen

def test_cloud_workflow():
    print("="*60)
    print("PROBANDO WORKFLOW COMPLETO EN NUBE SEGURA (cloud_db.py)")
    print("="*60)
    
    docx_sample = r"C:/Users/cgalvan/.gemini/antigravity/brain/d8ba3ed8-7506-4828-bfd0-144e2139d5f5/.user_uploaded/media_1793848564329_69f18b45.docx"
    parsed = parser.parse_solicitud_input(file_source=docx_sample)
    
    conn, engine = cdb.get_db_connection()
    c = conn.cursor()
    
    # Limpiar test previo
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
    
    for idx, inst in enumerate(parsed['instrumentos'], 1):
        c.execute("""
        INSERT INTO partidas (
            sub_solicitud_id, solicitud_id, numero_partida, descripcion_equipo,
            marca, modelo, no_serie, alcance_solicitado, descripcion_servicio,
            certificado_anterior, magnitud, id_interno, condiciones_particulares,
            tiempo_dias_habiles, precio_unitario, precio_total, es_no_realizable
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 5, 4500, 4500, 0)
        """, (
            sub_id, sol_id, idx, inst['descripcion'],
            inst['marca'], inst['modelo'], inst['serie'], inst['intervalo'], inst['descripcion'],
            inst['certificado_anterior'], inst['magnitud'], inst['id_interno'], inst['condiciones']
        ))
    conn.commit()
    
    # Simular Cotización
    c.execute("UPDATE sub_solicitudes_at SET estado = 'COMPLETADA' WHERE id = ?", (sub_id,))
    no_cot = cdb.get_next_cotizacion_number()
    c.execute("UPDATE solicitudes_master SET no_cotizacion = ?, estado = 'COTIZACION_ENVIADA' WHERE id = ?", (no_cot, sol_id))
    conn.commit()
    
    # Simular Aceptación del cliente y pase a programación
    c.execute("UPDATE partidas SET aceptada_cliente = 1 WHERE solicitud_id = ?", (sol_id,))
    c.execute("UPDATE solicitudes_master SET estado = 'EN_PROGRAMACION' WHERE id = ?", (sol_id,))
    c.execute("UPDATE sub_solicitudes_at SET estado = 'EN_PROGRAMACION' WHERE id = ?", (sub_id,))
    conn.commit()
    
    # Simular Programación de AT-01
    f_ini = datetime(2026, 6, 8)
    f_rec = cdb.restar_dias_habiles(f_ini, 2)
    f_fin = cdb.sumar_dias_habiles(f_ini, 5)
    f_lim = datetime(2026, 6, 29)
    
    c.execute("""
    UPDATE sub_solicitudes_at
    SET estado = 'PROGRAMA_PROPUESTO', fecha_recepcion_prog = ?, fecha_inicio_prog = ?, fecha_entrega_prog = ?, fecha_limite_prog = ?
    WHERE id = ?
    """, (f_rec.strftime("%Y-%m-%d"), f_ini.strftime("%Y-%m-%d"), f_fin.strftime("%Y-%m-%d"), f_lim.strftime("%Y-%m-%d"), sub_id))
    c.execute("""
    UPDATE partidas
    SET fecha_recepcion_equipo = ?, fecha_inicio_calibracion = ?, fecha_entrega_equipo = ?, fecha_limite_aceptacion = ?
    WHERE sub_solicitud_id = ?
    """, (f_rec.strftime("%Y-%m-%d"), f_ini.strftime("%Y-%m-%d"), f_fin.strftime("%Y-%m-%d"), f_lim.strftime("%Y-%m-%d"), sub_id))
    conn.commit()
    
    # Confirmación final y archivo
    c.execute("""
    UPDATE solicitudes_master
    SET estado = 'CONFIRMADA_CONCLUIDA', modalidad_retorno = 'RECOLECCION_CENAM',
        representante_legal_cenam = 'Lic. Miguel Angel Torres', fecha_confirmacion_programa = ?
    WHERE id = ?
    """, (now_str, sol_id))
    c.execute("UPDATE sub_solicitudes_at SET estado = 'PROGRAMA_CONFIRMADO' WHERE id = ?", (sub_id,))
    conn.commit()
    # Test PDF Generation from Supabase real rows
    print("Testing PDF Generation from Supabase real rows...")
    conn, engine = cdb.get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM solicitudes_master WHERE id = ?", (sol_id,))
    s_row = c.fetchone()
    c.execute("SELECT * FROM partidas WHERE solicitud_id = ?", (sol_id,))
    parts_rows = c.fetchall()
    
    # 1. Cotizacion PDF
    cot_pdf_path = f"generated_docs/Cotizacion_Cloud_{s_row['no_folio'].replace('-', '_')}.pdf"
    pdf_gen.generate_cotizacion_pdf(dict(s_row), [dict(p) for p in parts_rows], cot_pdf_path)
    assert os.path.exists(cot_pdf_path) and os.path.getsize(cot_pdf_path) > 1000, "Cotizacion PDF from Supabase row failed"
    print(f"  -> Cotización Supabase PDF OK ({os.path.getsize(cot_pdf_path)} bytes)")
    
    # 2. Programacion PDF (Exact line 720 logic)
    c.execute("SELECT sub.*, a.nombre as nombre_area FROM sub_solicitudes_at sub LEFT JOIN areas_tecnicas a ON sub.clave_area = a.clave WHERE sub.solicitud_id = ?", (sol_id,))
    subs_rows = c.fetchall()
    
    for sub in subs_rows:
        c.execute("SELECT * FROM partidas WHERE sub_solicitud_id = ? AND aceptada_cliente = 1", (sub['id'],))
        sub_parts = c.fetchall()
        if sub_parts:
            prog_pdf_path = f"generated_docs/Contrato_Programacion_Cloud_{s_row['no_folio'].replace('-', '_')}_{sub['clave_area']}.pdf"
            sol_d = dict(s_row)
            sol_d['modalidad_retorno'] = 'RECOLECCION_CENAM'
            sol_d['direccion_servicio_sitio'] = 'Planta San Juan del Rio'
            sol_d['condiciones_acceso_planta'] = 'Casco, chaleco'
            pdf_gen.generate_programacion_pdf(
                sol_d, dict(sub), [dict(p) for p in sub_parts],
                tipo='IN_SITU' if s_row['es_in_situ'] else 'CENAM',
                filepath=prog_pdf_path,
                rep_legal_cenam="DR. CARLOS GONZALEZ"
            )
            assert os.path.exists(prog_pdf_path) and os.path.getsize(prog_pdf_path) > 1000, "Programacion PDF from Supabase row failed"
            print(f"  -> Programación Supabase PDF OK: {sub['clave_area']} ({os.path.getsize(prog_pdf_path)} bytes)")
    
    conn.close()
    
    cdb.log_auditoria("ssi@cenam.mx", "CONFIRMAR_SERVICIO", "solicitudes_master", sol_id, f"Servicio con Folio {parsed['no_folio']} formalizado y reservado.")
    
    print("EXITO: Workflow en Nube Segura (cloud_db.py) y generacion de PDFs completado y auditado al 100%.")

if __name__ == '__main__':
    test_cloud_workflow()
