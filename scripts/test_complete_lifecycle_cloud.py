import os
import sys
from datetime import datetime, date, timedelta
from decimal import Decimal

# Add nube_segura to path
sys.path.insert(0, os.path.abspath("nube_segura"))
import request_parser as parser
import cloud_db as cdb
import pdf_generator as pdf_gen

def test_full_cloud_lifecycle():
    print("="*70)
    print("PRUEBA EXHAUSTIVA DE CICLO COMPLETO EN SUPABASE POSTGRESQL (NUBE SEGURA)")
    print("="*70)
    
    # 0. Verificar conexión a Supabase y pooler
    print("\n[Paso 0] Verificando salud de la conexión y catálogo en la Nube...")
    db_url = cdb.get_database_url()
    ok, msg, info = cdb.test_postgres_connection(db_url)
    print(f"  Test de conexión Supabase: {msg}")
    assert ok, f"Error al conectar con Supabase: {msg}"
    
    # 1. Recepción y Parseo desde DOCX real del usuario
    print("\n[Etapa 1: Recepción de Solicitud]")
    sample_path = r"C:/Users/cgalvan/.gemini/antigravity/brain/d8ba3ed8-7506-4828-bfd0-144e2139d5f5/.user_uploaded/media_1793848564329_69f18b45.docx"
    parsed = parser.parse_solicitud_input(file_source=sample_path)
    print(f"  Solicitud extraída: {parsed['no_solicitud']} | Folio: {parsed['no_folio']}")
    print(f"  Cliente: {parsed['empresa']} | Contacto: {parsed['contacto']}")
    print(f"  Instrumentos extraídos: {len(parsed['instrumentos'])}")
    assert parsed['no_solicitud'].endswith('PR'), "No. Solicitud debe terminar en PR"
    assert parsed['no_folio'].endswith('PR'), "No. Folio debe terminar en PR"
    assert len(parsed['instrumentos']) == 4, "Deben haberse extraído 4 instrumentos"
    
    conn, engine = cdb.get_db_connection()
    c = conn.cursor()
    
    # Limpieza de corridas previas para idempotencia
    c.execute("DELETE FROM partidas WHERE solicitud_id IN (SELECT id FROM solicitudes_master WHERE no_folio = ?)", (parsed['no_folio'],))
    c.execute("DELETE FROM sub_solicitudes_at WHERE solicitud_id IN (SELECT id FROM solicitudes_master WHERE no_folio = ?)", (parsed['no_folio'],))
    c.execute("DELETE FROM solicitudes_master WHERE no_folio = ?", (parsed['no_folio'],))
    conn.commit()
    
    # Inserción en solicitudes_master
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
    
    # Turnado a División 740 (Dimensional)
    c.execute("""
    INSERT INTO sub_solicitudes_at (solicitud_id, clave_area, estado, fecha_asignacion, fecha_limite_sla)
    VALUES (?, '740', 'ASIGNADA', ?, ?)
    """, (sol_id, now_str, (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d")))
    sub_id = c.lastrowid
    
    for idx, inst in enumerate(parsed['instrumentos'], 1):
        c.execute("""
        INSERT INTO partidas (
            sub_solicitud_id, solicitud_id, numero_partida, descripcion_equipo,
            marca, modelo, no_serie, alcance_solicitado, descripcion_servicio,
            certificado_anterior, magnitud, id_interno, condiciones_particulares,
            tiempo_dias_habiles, precio_unitario, precio_total, es_no_realizable
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 5, 4850.50, 4850.50, 0)
        """, (
            sub_id, sol_id, idx, inst['descripcion'],
            inst['marca'], inst['modelo'], inst['serie'], inst['intervalo'], inst['descripcion'],
            inst['certificado_anterior'], inst['magnitud'], inst['id_interno'], inst['condiciones']
        ))
    conn.commit()
    print("  -> Solicitud guardada y turnada a AT-01 exitosamente.")
    
    # 2. Etapa 2: Cotización por CS-AT y Consolidación por SSI
    print("\n[Etapa 2: Cotización Metrológica]")
    c.execute("UPDATE sub_solicitudes_at SET estado = 'COMPLETADA' WHERE id = ?", (sub_id,))
    next_cot = cdb.get_next_cotizacion_number()
    assert next_cot.endswith('PR'), "No. Cotización debe llevar sufijo PR"
    print(f"  No. Cotización asignado por SSI: {next_cot}")
    
    c.execute("UPDATE solicitudes_master SET no_cotizacion = ?, estado = 'COTIZACION_ENVIADA' WHERE id = ?", (next_cot, sol_id))
    conn.commit()
    
    # Generar PDF oficial de Cotización
    c.execute("SELECT * FROM solicitudes_master WHERE id = ?", (sol_id,))
    s_dict = dict(c.fetchone())
    c.execute("SELECT * FROM partidas WHERE solicitud_id = ?", (sol_id,))
    p_dicts = [dict(row) for row in c.fetchall()]
    
    os.makedirs("generated_docs", exist_ok=True)
    cot_pdf = f"generated_docs/Cotizacion_Prueba_{s_dict['no_folio'].replace('-', '_')}.pdf"
    pdf_gen.generate_cotizacion_pdf(s_dict, p_dicts, cot_pdf)
    assert os.path.exists(cot_pdf) and os.path.getsize(cot_pdf) > 1000, "Cotización PDF falló"
    print(f"  -> PDF Oficial de Cotización generado: {cot_pdf} ({os.path.getsize(cot_pdf)} bytes)")
    
    # 3. Etapa 3: Programación por CS-AT
    print("\n[Etapa 3: Programación de Calibración por Área Técnica]")
    # Cliente acepta todas las partidas
    c.execute("UPDATE partidas SET aceptada_cliente = 1 WHERE solicitud_id = ?", (sol_id,))
    c.execute("UPDATE solicitudes_master SET estado = 'EN_PROGRAMACION' WHERE id = ?", (sol_id,))
    c.execute("UPDATE sub_solicitudes_at SET estado = 'EN_PROGRAMACION' WHERE id = ?", (sub_id,))
    conn.commit()
    
    # CS-AT define fechas
    # Inicio: 2026-06-08 (Lunes)
    # Recepción automática: 2 días hábiles antes -> 2026-06-04 (Jueves)
    f_inicio = datetime(2026, 6, 8)
    f_recepcion = cdb.restar_dias_habiles(f_inicio, 2)
    f_fin = cdb.sumar_dias_habiles(f_inicio, 5)
    f_limite = datetime(2026, 6, 29)
    
    assert f_recepcion.weekday() == 3, f"Fecha de recepción debe ser Jueves (weekday 3), fue {f_recepcion.weekday()}"
    print(f"  Cálculo regla de calidad CENAM (-2 días hábiles):")
    print(f"    Fecha inicio calibración: {f_inicio.strftime('%Y-%m-%d')} ({f_inicio.strftime('%A')})")
    print(f"    Fecha recepción calculada: {f_recepcion.strftime('%Y-%m-%d')} ({f_recepcion.strftime('%A')})")
    print(f"    Fecha entrega: {f_fin.strftime('%Y-%m-%d')}")
    print(f"    Fecha límite aceptación: {f_limite.strftime('%Y-%m-%d')}")
    
    c.execute("""
    UPDATE sub_solicitudes_at
    SET estado = 'PROGRAMA_PROPUESTO', fecha_recepcion_prog = ?, fecha_inicio_prog = ?,
        fecha_entrega_prog = ?, fecha_limite_prog = ?
    WHERE id = ?
    """, (f_recepcion.strftime("%Y-%m-%d"), f_inicio.strftime("%Y-%m-%d"), f_fin.strftime("%Y-%m-%d"), f_limite.strftime("%Y-%m-%d"), sub_id))
    c.execute("""
    UPDATE partidas
    SET fecha_recepcion_equipo = ?, fecha_inicio_calibracion = ?, fecha_entrega_equipo = ?, fecha_limite_aceptacion = ?
    WHERE sub_solicitud_id = ?
    """, (f_recepcion.strftime("%Y-%m-%d"), f_inicio.strftime("%Y-%m-%d"), f_fin.strftime("%Y-%m-%d"), f_limite.strftime("%Y-%m-%d"), sub_id))
    conn.commit()
    print("  -> CS-AT envió propuesta de programa con fechas.")
    
    # 4. Etapa 4: Confirmación y Formalización de Contrato
    print("\n[Etapa 4: Confirmación y Formalización]")
    c.execute("SELECT * FROM solicitudes_master WHERE id = ?", (sol_id,))
    s_upd = dict(c.fetchone())
    c.execute("SELECT sub.*, a.nombre as nombre_area FROM sub_solicitudes_at sub LEFT JOIN areas_tecnicas a ON sub.clave_area = a.clave WHERE sub.id = ?", (sub_id,))
    sub_row = dict(c.fetchone())
    c.execute("SELECT * FROM partidas WHERE sub_solicitud_id = ? AND aceptada_cliente = 1", (sub_id,))
    parts_acep = [dict(p) for p in c.fetchall()]
    
    # Simular descarga de PDF de programación (línea 720 de app_cloud.py)
    prog_pdf = f"generated_docs/Contrato_Programacion_Prueba_{s_upd['no_folio'].replace('-', '_')}_{sub_row['clave_area']}.pdf"
    s_upd['modalidad_retorno'] = 'RECOLECCION_CENAM'
    s_upd['direccion_servicio_sitio'] = 'Instalaciones CENAM'
    s_upd['condiciones_acceso_planta'] = 'N/A'
    
    pdf_gen.generate_programacion_pdf(
        s_upd, sub_row, parts_acep,
        tipo='IN_SITU' if s_upd['es_in_situ'] else 'CENAM',
        filepath=prog_pdf,
        rep_legal_cenam="DR. CARLOS GONZALEZ"
    )
    assert os.path.exists(prog_pdf) and os.path.getsize(prog_pdf) > 1000, "Programación PDF falló"
    print(f"  -> Contrato y Programación PDF generado exitosamente: {prog_pdf} ({os.path.getsize(prog_pdf)} bytes)")
    
    # Confirmar y reservar
    c.execute("""
    UPDATE solicitudes_master
    SET estado = 'CONFIRMADA_CONCLUIDA', modalidad_retorno = ?, representante_legal_cenam = ?,
        direccion_servicio_sitio = ?, condiciones_acceso_planta = ?, fecha_confirmacion_programa = ?
    WHERE id = ?
    """, ('RECOLECCION_CENAM', 'DR. CARLOS GONZALEZ', 'Instalaciones CENAM', 'N/A', now_str, sol_id))
    c.execute("UPDATE sub_solicitudes_at SET estado = 'PROGRAMA_CONFIRMADO' WHERE solicitud_id = ?", (sol_id,))
    conn.commit()
    
    # 5. Verificación en Calendario de CS-AT
    c.execute("""
    SELECT s.no_folio, s.no_cotizacion, s.cliente, sub.fecha_recepcion_prog, sub.fecha_inicio_prog, sub.fecha_entrega_prog
    FROM sub_solicitudes_at sub
    JOIN solicitudes_master s ON sub.solicitud_id = s.id
    WHERE sub.clave_area = '740' AND sub.estado = 'PROGRAMA_CONFIRMADO' AND s.id = ?
    """, (sol_id,))
    cal_row = c.fetchone()
    assert cal_row is not None, "El registro confirmado debe aparecer en el Calendario de AT-01"
    print(f"  -> Verificado en Calendario de Laboratorio AT-01:")
    print(f"     Folio: {cal_row['no_folio']} | Cotización: {cal_row['no_cotizacion']} | Recepción: {cal_row['fecha_recepcion_prog']} | Inicio: {cal_row['fecha_inicio_prog']}")
    
    conn.close()
    
    print("\n" + "="*70)
    print("EXITO TOTAL: El ciclo completo de 4 etapas en Supabase PostgreSQL")
    print("ha sido probado y validado con 100% de éxito.")
    print("="*70)

if __name__ == '__main__':
    test_full_cloud_lifecycle()
