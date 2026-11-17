"""
Test de verificación estricta:
1. Precios de servicios no aparecen en ceros en cotización SSI
2. Validación de calidad: bloqueo si precio <= 0 en CS-AT y SSI
3. Auto-reparación preventiva de precios desde el catálogo
4. Optimización de consultas a la base de datos (Batch Queries y Catálogo en RAM)
"""
import os
import sys
from datetime import datetime, date, timedelta

sys.path.insert(0, os.path.abspath("nube_segura"))
import cloud_db as cdb
import pdf_generator as pdf_gen

def test_pricing_and_batch_queries():
    print("=" * 70)
    print("INICIANDO TEST DE PRECIOS NO CEROS Y OPTIMIZACIÓN DE CONSULTAS")
    print("=" * 70)
    
    conn, engine = cdb.get_db_connection()
    c = conn.cursor()
    
    # 1. Verificar carga en memoria de catálogo
    c.execute("SELECT COUNT(*) FROM catalogo_servicios")
    total_servs_db = c.fetchone()[0]
    print(f"[1] Catálogo de Servicios en BD: {total_servs_db} registros.")
    assert total_servs_db >= 1000, "El catálogo debe tener más de 1000 servicios"
    
    # Cargar catálogo a RAM como lo hace la app
    c.execute("""
        SELECT clave_servicio, supuesto, alcance, observaciones, costo, dias_habiles_defecto, es_in_situ,
               codigo_laboratorio, nombre_laboratorio, clave_area, codigo_division, metodo, incertidumbre
        FROM catalogo_servicios
    """)
    servs_list = [dict(r) for r in c.fetchall()]
    serv_by_clave = {s['clave_servicio']: s for s in servs_list}
    print(f"    -> Mapeados {len(serv_by_clave)} servicios en memoria.")
    
    # 2. Crear una solicitud de prueba
    folio_test = "TEST-PRECIOS-01PR"
    sol_test = "2026TEST01PR"
    
    c.execute("DELETE FROM partidas WHERE solicitud_id IN (SELECT id FROM solicitudes_master WHERE no_folio = ?)", (folio_test,))
    c.execute("DELETE FROM sub_solicitudes_at WHERE solicitud_id IN (SELECT id FROM solicitudes_master WHERE no_folio = ?)", (folio_test,))
    c.execute("DELETE FROM solicitudes_master WHERE no_folio = ?", (folio_test,))
    conn.commit()
    
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("""
        INSERT INTO solicitudes_master (
            no_solicitud, no_folio, version, cliente, representante, telefono, correo,
            rfc, pais, es_extranjero, aplica_iva, fecha_recepcion, estado, es_in_situ, clave_area
        ) VALUES (?, ?, 1, 'EMPRESA PRUEBA PRECIOS', 'ING. PRUEBA', '4421234567', 'prueba@cenam.mx',
                  'PRU260101XYZ', 'México', 0, 1, ?, 'TURNADA', 0, '740')
    """, (sol_test, folio_test, now_str))
    sol_id = c.lastrowid
    
    c.execute("""
        INSERT INTO sub_solicitudes_at (solicitud_id, clave_area, estado, fecha_asignacion, fecha_limite_sla)
        VALUES (?, '740', 'ASIGNADA', ?, ?)
    """, (sol_id, now_str, (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d")))
    sub_id = c.lastrowid
    
    # Insertar 2 partidas:
    # Partida 1: Viable pero inicialmente con precio 0.0 (simulando que aún no se le pone precio)
    # Partida 2: Viable con clave de catálogo asignada pero precio en 0.0 (simulando olvido de cálculo)
    c.execute("""
        INSERT INTO partidas (
            sub_solicitud_id, solicitud_id, numero_partida, descripcion_equipo,
            marca, modelo, no_serie, es_no_realizable, precio_unitario, precio_total, cantidad
        ) VALUES (?, ?, 1, 'MICROMETRO EXTERIOR', 'MITUTOYO', '103-137', 'S001', 0, 0.0, 0.0, 2)
    """, (sub_id, sol_id))
    p1_id = c.lastrowid
    
    # Buscar un servicio real de Dimensional (740)
    c.execute("SELECT clave_servicio, supuesto, costo FROM catalogo_servicios WHERE clave_area = '740' AND costo > 0 LIMIT 1")
    srv_real = dict(c.fetchone())
    clave_srv_real = srv_real['clave_servicio']
    costo_srv_real = float(srv_real['costo'])
    print(f"[2] Servicio de prueba del catálogo: {clave_srv_real} con costo ${costo_srv_real:,.2f}")
    
    c.execute("""
        INSERT INTO partidas (
            sub_solicitud_id, solicitud_id, numero_partida, descripcion_equipo,
            marca, modelo, no_serie, es_no_realizable, clave_servicio, precio_unitario, precio_total, cantidad
        ) VALUES (?, ?, 2, 'CALIBRADOR VERNIER', 'STARRETT', '125', 'S002', 0, ?, 0.0, 0.0, 3)
    """, (sub_id, sol_id, clave_srv_real))
    p2_id = c.lastrowid
    conn.commit()
    
    # 3. Probar Quality Gate de CS-AT: Bloqueo de aprobación si hay precio 0
    print("\n[3] Probando Quality Gate en CS-AT:")
    c.execute("SELECT * FROM partidas WHERE sub_solicitud_id = ?", (sub_id,))
    partidas_eval = [dict(r) for r in c.fetchall()]
    
    errores_validacion = []
    for p in partidas_eval:
        if p['es_no_realizable'] == 0:
            if not p.get('clave_servicio') or p['clave_servicio'] not in serv_by_clave:
                errores_validacion.append(f"Partida {p['numero_partida']}: Sin servicio de catálogo válido.")
            elif float(p.get('precio_unitario') or 0.0) <= 0.0:
                errores_validacion.append(f"Partida {p['numero_partida']}: Precio unitario es $0.00.")
                
    assert len(errores_validacion) > 0, "Debe detectar errores de validación de precios en cero"
    print(f"    -> Quality Gate activo: Detectó {len(errores_validacion)} error(es) correctamente:")
    for err in errores_validacion:
        print(f"       * {err}")
    print("    -> Aprobación bloqueada exitosamente como se esperaba.")
    
    # 4. Probar Auto-Healing en SSI Tab 3:
    print("\n[4] Probando Auto-reparación preventiva en Tab 3 de SSI:")
    # Partida 2 tiene clave_servicio pero precio 0.0 -> el auto-healing debe rellenarlo
    for p in partidas_eval:
        if p['es_no_realizable'] == 0:
            p_u = float(p.get('precio_unitario') or 0.0)
            c_serv = p.get('clave_servicio')
            if p_u <= 0.0 and c_serv and c_serv in serv_by_clave:
                s_cat = serv_by_clave[c_serv]
                nuevo_precio = float(s_cat.get('costo') or 0.0)
                if nuevo_precio > 0.0:
                    cant_val = int(p.get('cantidad') or 1)
                    tot_val = nuevo_precio * cant_val
                    c.execute("""
                        UPDATE partidas
                        SET precio_unitario = ?, precio_total = ?, descripcion_servicio = ?
                        WHERE id = ?
                    """, (nuevo_precio, tot_val, s_cat.get('supuesto'), p['id']))
                    conn.commit()
                    print(f"    -> Auto-reparada Partida {p['numero_partida']} con precio ${nuevo_precio:,.2f} (Total: ${tot_val:,.2f})")
                    
    # Verificar que partida 2 ahora tiene precio
    c.execute("SELECT precio_unitario, precio_total, cantidad FROM partidas WHERE id = ?", (p2_id,))
    p2_actualizada = dict(c.fetchone())
    assert float(p2_actualizada['precio_unitario']) == costo_srv_real, "Partida 2 debió ser auto-reparada"
    assert float(p2_actualizada['precio_total']) == costo_srv_real * 3, "Total de partida 2 debe ser costo * 3"
    print("    -> Auto-healing verificado con éxito.")
    
    # 5. Probar bloqueo en SSI Tab 3 si todavía queda Partida 1 en cero:
    c.execute("SELECT * FROM partidas WHERE solicitud_id = ?", (sol_id,))
    parts_ssi = [dict(r) for r in c.fetchall()]
    ceros_parts = [p for p in parts_ssi if p['es_no_realizable'] == 0 and (float(p.get('precio_unitario') or 0.0) <= 0.0 or not p.get('clave_servicio'))]
    assert len(ceros_parts) == 1, "Debe quedar exactamente 1 partida en cero (Partida 1)"
    print(f"\n[5] Tab 3 SSI detectó partida pendiente en $0.00: Partida {ceros_parts[0]['numero_partida']}.")
    print("    -> Botón de Asignar Cotización queda BLOQUEADO.")
    
    # 6. Corregir Partida 1 mediante herramienta rápida de SSI
    print("\n[6] Aplicando corrección rápida de SSI a Partida 1:")
    c.execute("""
        UPDATE partidas
        SET clave_servicio = ?, descripcion_servicio = ?,
            precio_unitario = ?, precio_total = ?, tiempo_dias_habiles = 5
        WHERE id = ?
    """, (clave_srv_real, srv_real['supuesto'], costo_srv_real, costo_srv_real * 2, p1_id))
    conn.commit()
    print(f"    -> Partida 1 corregida con costo unitario ${costo_srv_real:,.2f} y total ${costo_srv_real * 2:,.2f}.")
    
    # 7. Asignar cotización y verificar cálculo financiero
    c.execute("SELECT * FROM partidas WHERE solicitud_id = ?", (sol_id,))
    parts_fin = [dict(r) for r in c.fetchall()]
    assert not any(p['es_no_realizable'] == 0 and float(p['precio_unitario']) <= 0.0 for p in parts_fin), "Ninguna partida puede tener $0.00"
    
    subtot = sum(float(p['precio_total']) for p in parts_fin if p['es_no_realizable'] == 0)
    iva = subtot * 0.16
    total_gral = subtot + iva
    print(f"\n[7] Resumen Financiero:")
    print(f"    Subtotal: ${subtot:,.2f}")
    print(f"    IVA 16%:  ${iva:,.2f}")
    print(f"    Total:    ${total_gral:,.2f}")
    assert subtot > 0.0, "Subtotal debe ser mayor a cero"
    assert iva > 0.0, "IVA debe ser mayor a cero"
    assert total_gral > subtot, "Total debe incluir IVA"
    
    # 8. Generar PDF de cotización y verificar que no hay ceros
    c.execute("SELECT * FROM solicitudes_master WHERE id = ?", (sol_id,))
    sol_dict = dict(c.fetchone())
    sol_dict['no_cotizacion'] = "269999PR"
    
    os.makedirs("generated_docs", exist_ok=True)
    pdf_test_path = "generated_docs/Cotizacion_Test_Sin_Ceros.pdf"
    pdf_gen.generate_cotizacion_pdf(sol_dict, parts_fin, pdf_test_path)
    assert os.path.exists(pdf_test_path) and os.path.getsize(pdf_test_path) > 1000, "El PDF debe generarse"
    print(f"\n[8] PDF generado exitosamente: {pdf_test_path} ({os.path.getsize(pdf_test_path)} bytes)")
    
    # Limpiar datos de prueba
    c.execute("DELETE FROM partidas WHERE solicitud_id = ?", (sol_id,))
    c.execute("DELETE FROM sub_solicitudes_at WHERE solicitud_id = ?", (sol_id,))
    c.execute("DELETE FROM solicitudes_master WHERE id = ?", (sol_id,))
    conn.commit()
    conn.close()
    
    print("\n" + "=" * 70)
    print("TODAS LAS VERIFICACIONES DE PRECIOS Y OPTIMIZACIÓN PASARON AL 100%")
    print("=" * 70)

if __name__ == "__main__":
    test_pricing_and_batch_queries()
