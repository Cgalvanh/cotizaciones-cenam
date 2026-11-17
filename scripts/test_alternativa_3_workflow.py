import os, sys
sys.path.insert(0, os.path.abspath('.'))
from dotenv import load_dotenv
load_dotenv('.env')

from nube_segura import cloud_db as cdb
from nube_segura import pdf_generator as pdf_gen

def test_alternativa_3():
    print("=" * 70)
    print("VERIFICACIÓN DE ALTERNATIVA 3: 1 FOLIO -> N SOLICITUDES + SEPARACIÓN IN SITU")
    print("=" * 70)

    # 1. Verificar catálogo oficial de áreas
    areas = cdb.get_areas_tecnicas()
    print(f"\n1. Catálogo de Áreas Oficiales ({len(areas)} divisiones):")
    claves = [a['clave'] for a in areas]
    assert '740' in claves and '730' in claves and '410' in claves, "Faltan claves numéricas oficiales"
    for a in areas[:5]:
        print(f"   • [{a['clave']}] {a['nombre']}")

    # 2. Recepción SSI: Registro de Expediente con partidas multiarea y partidas in situ
    print("\n2. Simulando Recepción SSI de cliente con múltiples instrumentos...")
    cliente_test = {
        "cliente": "LABORATORIOS INDUSTRIALES DEL NORTE S.A. DE C.V.",
        "representante": "Ing. Sofía Morales",
        "telefono": "8181234567",
        "correo": "sofia.morales@labnorte.com",
        "rfc": "LIN890412AB1",
        "pais": "México",
        "es_extranjero": False,
        "aplica_iva": True
    }

    instrumentos = [
        # Partida 1: Dimensional (740) - LAB CENAM
        {
            "desc": "Calibrador pie de rey digital",
            "marca": "Mitutoyo",
            "modelo": "500-196",
            "serie": "SN-DIM-01",
            "alcance": "0 a 150 mm",
            "clave_area": "740",
            "es_in_situ": 0
        },
        # Partida 2: Dimensional (740) - LAB CENAM
        {
            "desc": "Micrómetro de exteriores",
            "marca": "Mitutoyo",
            "modelo": "103-137",
            "serie": "SN-DIM-02",
            "alcance": "0 a 25 mm",
            "clave_area": "740",
            "es_in_situ": 0
        },
        # Partida 3: Dimensional (740) - IN SITU (Con Viáticos)
        {
            "desc": "Máquina de Medición por Coordenadas (CMM)",
            "marca": "Zeiss",
            "modelo": "Prismo 7",
            "serie": "SN-DIM-INSITU",
            "alcance": "1000 x 1200 x 700 mm",
            "clave_area": "740",
            "es_in_situ": 1
        },
        # Partida 4: Masa (730) - LAB CENAM
        {
            "desc": "Juego de pesas clase E2",
            "marca": "Troemner",
            "modelo": "E2-SET",
            "serie": "SN-MASA-01",
            "alcance": "1 mg a 1 kg",
            "clave_area": "730",
            "es_in_situ": 0
        },
        # Partida 5: Eléctrica (410) - LAB CENAM
        {
            "desc": "Multímetro de referencia 8.5 dígitos",
            "marca": "Fluke",
            "modelo": "8508A",
            "serie": "SN-ELEC-01",
            "alcance": "100 mV a 1000 V",
            "clave_area": "410",
            "es_in_situ": 0
        }
    ]

    res_exp = cdb.crear_expediente_y_solicitudes(cliente_test, instrumentos, "ssi@cenam.mx")
    folio = res_exp["no_folio"]
    sols = res_exp["solicitudes_creadas"]

    print(f"   [OK] Expediente creado con EXITO:")
    print(f"   * Folio Unico Asignado: {folio}")
    print(f"   * Total de Solicitudes Hijas Generadas: {len(sols)}")
    assert len(sols) == 4, f"Se esperaban 4 solicitudes (740 LAB, 740 IN SITU, 730 LAB, 410 LAB), se obtuvieron {len(sols)}"

    for s in sols:
        mod = "IN SITU" if s['es_in_situ'] else "LAB CENAM"
        print(f"     -> Solicitud {s['no_solicitud']} | Division: {s['clave_area']} | Modalidad: {mod} | Partidas: {s['total_partidas']}")

    # 3. Probar la separación dinámica IN SITU en la bandeja del Especialista
    print("\n3. Simulando Separacion IN SITU en la bandeja de AT...")
    sol_dim_lab = next(s for s in sols if s['clave_area'] == '740' and s['es_in_situ'] == 0)
    
    conn, eng = cdb.get_db_connection()
    c = conn.cursor()
    c.execute("SELECT id, descripcion_equipo FROM partidas WHERE solicitud_id = ? ORDER BY id", (sol_dim_lab['solicitud_id'],))
    parts_dim = c.fetchall()
    conn.close()

    assert len(parts_dim) == 2, "La solicitud 740 LAB debe tener 2 partidas"
    partida_a_mover = parts_dim[1]['id']

    res_sep = cdb.separar_partidas_in_situ(sol_dim_lab['solicitud_id'], [partida_a_mover], "especialista@cenam.mx")
    print(f"   [OK] Partida separada dinamicamente:")
    print(f"   * Folio que se conserva: {res_sep['no_folio']}")
    print(f"   * Nueva Solicitud IN SITU generada: {res_sep['nuevo_no_solicitud']}")
    assert res_sep['no_folio'] == folio, "El folio DEBE mantenerse para trazabilidad"

    # 4. Probar Vista del Expediente por Folio
    print("\n4. Consultando el Arbol del Expediente...")
    expedientes = cdb.get_expedientes_resumen()
    exp_actual = next((e for e in expedientes if e['no_folio'] == folio), None)
    assert exp_actual is not None, f"No se encontró el expediente {folio}"
    print(f"   [OK] Expediente {exp_actual['no_folio']} contiene ahora {len(exp_actual['solicitudes'])} solicitudes hijas:")
    for h in exp_actual['solicitudes']:
        mod_t = "IN SITU" if h['es_in_situ'] else "LAB CENAM"
        print(f"     |-- {h['no_solicitud']} | Div: {h['clave_area']} ({h['nombre_area']}) | {mod_t} | {h['total_partidas']} partida(s)")

    # 5. Generar y Validar Documentos Oficiales en Tamaño Carta con Logo y Pie de Página
    print("\n5. Generacion de Documentos Tamano Carta (8.5x11 in) con Logo y Pie Institucional...")
    os.makedirs("generated_docs", exist_ok=True)
    pdf_cot = f"generated_docs/Cotizacion_Expediente_{folio.replace('-', '_')}.pdf"
    
    conn, eng = cdb.get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM solicitudes_master WHERE no_folio = ? LIMIT 1", (folio,))
    s_row = dict(c.fetchone())
    c.execute("SELECT * FROM partidas WHERE solicitud_id = ?", (s_row['id'],))
    p_rows = [dict(r) for r in c.fetchall()]
    conn.close()

    pdf_gen.generate_cotizacion_pdf(s_row, p_rows, pdf_cot)
    assert os.path.exists(pdf_cot) and os.path.getsize(pdf_cot) > 5000, "Error en PDF de cotizacion"
    print(f"   [OK] PDF de Cotizacion generado: {pdf_cot} ({os.path.getsize(pdf_cot)} bytes)")

    sub_dummy = {"clave_area": s_row['clave_area'], "nombre_area": "Division de Metrologia Dimensional", "fecha_inicio_prog": "2026-06-08"}
    pdf_prog = f"generated_docs/Programacion_Expediente_{folio.replace('-', '_')}.pdf"
    pdf_gen.generate_programacion_pdf(s_row, sub_dummy, p_rows, tipo='CENAM', filepath=pdf_prog, rep_legal_cenam="DR. CARLOS GONZALEZ")
    assert os.path.exists(pdf_prog) and os.path.getsize(pdf_prog) > 5000, "Error en PDF de programacion"
    print(f"   [OK] PDF de Programacion generado: {pdf_prog} ({os.path.getsize(pdf_prog)} bytes)")

    print("\n" + "=" * 70)
    print("TODAS LAS PRUEBAS DE LA ALTERNATIVA 3 PASARON AL 100%")
    print("=" * 70)

if __name__ == '__main__':
    test_alternativa_3()
