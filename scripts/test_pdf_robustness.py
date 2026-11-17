import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from decimal import Decimal
from datetime import date, datetime
import pdf_generator as local_pdf
from nube_segura import pdf_generator as cloud_pdf

def run_tests():
    os.makedirs("generated_docs/test", exist_ok=True)
    
    mock_sol = {
        'id': 999,
        'no_folio': '9999-2026PR',
        'no_solicitud': '2026999PR',
        'no_cotizacion': '269999PR',
        'cliente': 'EMPRESA METROLOGICA DE PRUEBA SA DE CV',
        'representante': 'ING. JUAN PEREZ',
        'rfc': 'EMP990101XYZ',
        'telefono': '4421234567',
        'correo': 'juan.perez@empresa.mx',
        'pais': 'México',
        'es_in_situ': 0,
        'aplica_iva': 1,
        'version': 1,
        'fecha_emision': date.today(),
        'vigencia': date(2026, 12, 31),
        'vigencia_programacion': '3 semanas',
        'modalidad_retorno': 'MENSAJERIA_CLIENTE',
        'direccion_servicio_sitio': 'Planta Central Queretaro',
        'condiciones_acceso_planta': 'EPP, botas con casquillo, INE'
    }
    
    mock_sub = {
        'id': 888,
        'solicitud_id': 999,
        'clave_area': 'TEMPERATURA',
        'nombre_area': 'Dirección de Termometría',
        'fecha_recepcion_prog': date(2026, 11, 15),
        'fecha_inicio_prog': date(2026, 11, 17),
        'fecha_entrega_prog': date(2026, 11, 24),
        'fecha_limite_prog': date(2026, 11, 10),
        'estado': 'PROGRAMADA'
    }
    
    mock_partidas = [
        {
            'id': 101,
            'numero_partida': 1,
            'descripcion_servicio': 'Calibración de termómetro digital industrial',
            'alcance_solicitado': 'De -20 °C a 250 °C',
            'id_interno': 'TERM-001',
            'no_serie': 'SN-987654',
            'marca': 'Fluke',
            'modelo': '1524',
            'tiempo_dias_habiles': 5,
            'cantidad': 2,
            'precio_unitario': Decimal('4850.50'),
            'precio_total': Decimal('9701.00'),
            'es_no_realizable': 0,
            'fecha_recepcion_equipo': date(2026, 11, 15),
            'fecha_inicio_calibracion': date(2026, 11, 17),
            'fecha_fin_calibracion': date(2026, 11, 24),
            'fecha_limite_aceptacion': date(2026, 11, 10),
            'fecha_entrega_resultados': date(2026, 11, 24)
        },
        {
            'id': 102,
            'numero_partida': 2,
            'descripcion_servicio': 'Calibración de termopar tipo K',
            'alcance_solicitado': 'Hasta 1000 °C',
            'id_interno': 'TP-02',
            'no_serie': 'SN-112233',
            'marca': 'Omega',
            'modelo': 'K-STD',
            'tiempo_dias_habiles': 3,
            'cantidad': 1,
            'precio_unitario': Decimal('2350.00'),
            'precio_total': Decimal('2350.00'),
            'es_no_realizable': 0,
            'fecha_recepcion_equipo': None,
            'fecha_inicio_calibracion': None,
            'fecha_fin_calibracion': None,
            'fecha_limite_aceptacion': None,
            'fecha_entrega_resultados': None
        }
    ]
    
    mock_dsnr = [
        {
            'id': 103,
            'numero_partida': 3,
            'descripcion_equipo': 'Calibrador de radiación ultravioleta extrema',
            'marca': 'LaserTech',
            'modelo': 'UV-900',
            'no_serie': 'UV-001',
            'alcance_solicitado': '10 nm a 100 nm',
            'motivo_dsnr': 'CENAM no cuenta con patrón nacional en dicho intervalo UV extremo.'
        }
    ]
    
    print("Testing LOCAL PDF generator...")
    cot_loc = local_pdf.generate_cotizacion_pdf(mock_sol, mock_partidas, "generated_docs/test/test_cot_local.pdf")
    assert os.path.exists(cot_loc) and os.path.getsize(cot_loc) > 1000, "Local cotizacion PDF failed"
    print("  -> Cotización Local OK:", cot_loc, f"({os.path.getsize(cot_loc)} bytes)")
    
    prog_cenam_loc = local_pdf.generate_programacion_pdf(mock_sol, mock_sub, mock_partidas, tipo='CENAM', filepath="generated_docs/test/test_prog_cenam_loc.pdf", rep_legal_cenam="DR. CARLOS GONZALEZ")
    assert os.path.exists(prog_cenam_loc) and os.path.getsize(prog_cenam_loc) > 1000, "Local programacion CENAM PDF failed"
    print("  -> Programación CENAM Local OK:", prog_cenam_loc, f"({os.path.getsize(prog_cenam_loc)} bytes)")
    
    prog_insitu_loc = local_pdf.generate_programacion_pdf(mock_sol, mock_sub, mock_partidas, tipo='IN_SITU', filepath="generated_docs/test/test_prog_insitu_loc.pdf", rep_legal_cenam="")
    assert os.path.exists(prog_insitu_loc) and os.path.getsize(prog_insitu_loc) > 1000, "Local programacion IN_SITU PDF failed"
    print("  -> Programación IN_SITU Local OK:", prog_insitu_loc, f"({os.path.getsize(prog_insitu_loc)} bytes)")
    
    dsnr_loc = local_pdf.generate_dsnr_pdf(mock_sol, mock_dsnr, "Dirección de Metrología Óptica", "generated_docs/test/test_dsnr_loc.pdf")
    assert os.path.exists(dsnr_loc) and os.path.getsize(dsnr_loc) > 1000, "Local DSNR PDF failed"
    print("  -> DSNR Local OK:", dsnr_loc, f"({os.path.getsize(dsnr_loc)} bytes)")
    
    print("\nTesting CLOUD PDF generator...")
    cot_cloud = cloud_pdf.generate_cotizacion_pdf(mock_sol, mock_partidas, "generated_docs/test/test_cot_cloud.pdf")
    assert os.path.exists(cot_cloud) and os.path.getsize(cot_cloud) > 1000, "Cloud cotizacion PDF failed"
    print("  -> Cotización Cloud OK:", cot_cloud, f"({os.path.getsize(cot_cloud)} bytes)")
    
    prog_cenam_cloud = cloud_pdf.generate_programacion_pdf(mock_sol, mock_sub, mock_partidas, tipo='CENAM', filepath="generated_docs/test/test_prog_cenam_cloud.pdf", rep_legal_cenam="LIC. MARIO LOPEZ")
    assert os.path.exists(prog_cenam_cloud) and os.path.getsize(prog_cenam_cloud) > 1000, "Cloud programacion CENAM PDF failed"
    print("  -> Programación CENAM Cloud OK:", prog_cenam_cloud, f"({os.path.getsize(prog_cenam_cloud)} bytes)")
    
    prog_insitu_cloud = cloud_pdf.generate_programacion_pdf(mock_sol, mock_sub, mock_partidas, tipo='IN_SITU', filepath="generated_docs/test/test_prog_insitu_cloud.pdf", rep_legal_cenam="")
    assert os.path.exists(prog_insitu_cloud) and os.path.getsize(prog_insitu_cloud) > 1000, "Cloud programacion IN_SITU PDF failed"
    print("  -> Programación IN_SITU Cloud OK:", prog_insitu_cloud, f"({os.path.getsize(prog_insitu_cloud)} bytes)")
    
    dsnr_cloud = cloud_pdf.generate_dsnr_pdf(mock_sol, mock_dsnr, "Dirección de Metrología Óptica", "generated_docs/test/test_dsnr_cloud.pdf")
    assert os.path.exists(dsnr_cloud) and os.path.getsize(dsnr_cloud) > 1000, "Cloud DSNR PDF failed"
    print("  -> DSNR Cloud OK:", dsnr_cloud, f"({os.path.getsize(dsnr_cloud)} bytes)")
    
    print("\nALL PDF TESTS WITH DECIMAL AND DATE OBJECTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    run_tests()
