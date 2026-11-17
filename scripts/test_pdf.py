import os
import sys
sys.path.insert(0, os.path.abspath("."))
import pdf_generator as pdf_gen

os.makedirs("generated_docs", exist_ok=True)

solicitud_test = {
    "cliente": "SEÑALIZACION Y CONTROL DEL SURESTE",
    "representante": "ROSA DE LA CRUZ",
    "telefono": "938 105 7208",
    "correo": "compras@secont.mx",
    "rfc": "SCS-121208-QK4",
    "pais": "México",
    "no_solicitud": "2026009PR",
    "no_folio": "0009-2026PR",
    "no_cotizacion": "260544PR",
    "version": 1,
    "fecha_emision": "2026-11-04",
    "vigencia": "2026-12-31",
    "vigencia_programacion": "3 semanas",
    "modalidad_retorno": "RECOLECCION_CENAM",
    "aplica_iva": 1
}

sub_solicitud_test = {
    "clave_area": "AT-01",
    "nombre_area": "AT-01 - Metrología Dimensional",
    "fecha_inicio_prog": "2026-12-02",
    "fecha_recepcion_prog": "2026-11-30",
    "fecha_entrega_prog": "2026-12-10",
    "fecha_limite_prog": "2026-11-25"
}

partidas_test = [
    {
        "numero_partida": 1,
        "descripcion_equipo": "Regla de cristal",
        "descripcion_servicio": "Calibración de regla de cristal. Alcance: (0 a 50) mm",
        "marca": "Mitutoyo",
        "modelo": "172-116",
        "no_serie": "28719",
        "id_interno": "PR-D-17",
        "tiempo_dias_habiles": 5,
        "cantidad": 1,
        "precio_unitario": 8500.0,
        "precio_total": 8500.0,
        "fecha_recepcion_equipo": "2026-11-30",
        "fecha_inicio_calibracion": "2026-12-02",
        "fecha_entrega_equipo": "2026-12-09",
        "fecha_limite_aceptacion": "2026-11-25"
    },
    {
        "numero_partida": 2,
        "descripcion_equipo": "Regla de cristal",
        "descripcion_servicio": "Calibración de regla de cristal. Alcance: (0 a 300) mm",
        "marca": "Mitutoyo",
        "modelo": "HL2-300",
        "no_serie": "105092",
        "id_interno": "PR-D-18",
        "tiempo_dias_habiles": 5,
        "cantidad": 1,
        "precio_unitario": 12000.0,
        "precio_total": 12000.0,
        "fecha_recepcion_equipo": "2026-11-30",
        "fecha_inicio_calibracion": "2026-12-02",
        "fecha_entrega_equipo": "2026-12-09",
        "fecha_limite_aceptacion": "2026-11-25"
    }
]

# Probar generación de Cotización PDF
pdf_gen.generate_cotizacion_pdf(solicitud_test, partidas_test, "generated_docs/test_cotizacion.pdf")
print("Cotización PDF generada exitosamente.")

# Probar generación de Programación CENAM PDF
pdf_gen.generate_programacion_pdf(solicitud_test, sub_solicitud_test, partidas_test, tipo='CENAM', filepath="generated_docs/test_programacion_cenam.pdf", rep_legal_cenam="Lic. Juan Pérez Gómez")
print("Programación CENAM PDF generada exitosamente.")

# Probar generación de Programación IN SITU PDF
pdf_gen.generate_programacion_pdf(solicitud_test, sub_solicitud_test, partidas_test, tipo='IN_SITU', filepath="generated_docs/test_programacion_insitu.pdf", rep_legal_cenam="")
print("Programación IN SITU PDF generada exitosamente.")
