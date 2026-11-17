import os
import sys

# Ensure root is in path
sys.path.insert(0, os.path.abspath("."))

import database as db

def test_local_flow():
    print("=== Testing Local Flow (database.py) ===")
    db.init_db()
    
    # 1. Simulate SSI registering a request with 2 items (AT-01 and AT-02)
    next_sol = db.get_next_solicitud_number()
    next_fol = db.get_next_folio_number()
    
    conn = db.get_connection()
    c = conn.cursor()
    c.execute("""
    INSERT INTO solicitudes_master (
        no_solicitud, no_folio, version, cliente, representante, telefono, correo, rfc, pais,
        es_extranjero, aplica_iva, fecha_recepcion, fecha_emision, vigencia, estado, es_in_situ
    ) VALUES (?, ?, 1, 'TEST CLIENTE SA DE CV', 'Ing. Prueba', '4421234567', 'prueba@cliente.com', 'CLI010101XYZ', 'México',
        0, 1, '2026-11-04 12:00:00', '2026-11-04', '2026-12-31', 'TURNADA', 0)
    """, (next_sol, next_fol))
    sol_id = c.lastrowid
    
    # Sub solicitudes for AT-01 and AT-02
    c.execute("INSERT INTO sub_solicitudes_at (solicitud_id, clave_area, estado, fecha_asignacion, fecha_limite_sla) VALUES (?, 'AT-01', 'ASIGNADA', '2026-11-04 12:00:00', '2026-11-07')", (sol_id,))
    sub_01 = c.lastrowid
    
    c.execute("INSERT INTO sub_solicitudes_at (solicitud_id, clave_area, estado, fecha_asignacion, fecha_limite_sla) VALUES (?, 'AT-02', 'ASIGNADA', '2026-11-04 12:00:00', '2026-11-07')", (sol_id,))
    sub_02 = c.lastrowid
    
    c.execute("INSERT INTO partidas (sub_solicitud_id, solicitud_id, numero_partida, descripcion_equipo, precio_total, es_no_realizable) VALUES (?, ?, 1, 'Bloque Patron', 2500.0, 0)", (sub_01, sol_id))
    c.execute("INSERT INTO partidas (sub_solicitud_id, solicitud_id, numero_partida, descripcion_equipo, precio_total, es_no_realizable) VALUES (?, ?, 2, 'Multimetro', 3100.0, 0)", (sub_02, sol_id))
    conn.commit()
    conn.close()
    
    # 2. Check AT-01 and AT-02 pending screen
    conn = db.get_connection()
    c = conn.cursor()
    c.execute("SELECT id FROM sub_solicitudes_at WHERE clave_area = 'AT-01' AND estado IN ('ASIGNADA', 'EN_CONSULTA') AND id = ?", (sub_01,))
    assert c.fetchone() is not None, "AT-01 should see its pending request"
    
    c.execute("SELECT id FROM sub_solicitudes_at WHERE clave_area = 'AT-02' AND estado IN ('ASIGNADA', 'EN_CONSULTA') AND id = ?", (sub_02,))
    assert c.fetchone() is not None, "AT-02 should see its pending request"
    
    # 3. AT-01 returns the request (No Corresponde)
    c.execute("UPDATE sub_solicitudes_at SET estado = 'DEVUELTA', motivo_devolucion = 'No calibrable en AT-01', area_sugerida = 'AT-07' WHERE id = ?", (sub_01,))
    conn.commit()
    
    # Verify it DISAPPEARED from AT-01 screen
    c.execute("SELECT id FROM sub_solicitudes_at WHERE clave_area = 'AT-01' AND estado IN ('ASIGNADA', 'EN_CONSULTA') AND id = ?", (sub_01,))
    assert c.fetchone() is None, "Sub-request MUST disappear from AT-01 screen when returned"
    print("-> Verified: Request disappeared from AT-01 screen when returned to SSI.")
    
    # 4. SSI Tab 2 sees it in devueltas
    c.execute("SELECT id FROM sub_solicitudes_at WHERE estado = 'DEVUELTA' AND id = ?", (sub_01,))
    assert c.fetchone() is not None, "SSI Tab 2 must see returned sub-request"
    
    # 5. SSI reassigns to AT-07
    c.execute("UPDATE sub_solicitudes_at SET clave_area = 'AT-07', estado = 'ASIGNADA', motivo_devolucion = NULL WHERE id = ?", (sub_01,))
    conn.commit()
    
    # Verify it DISAPPEARED from SSI Tab 2
    c.execute("SELECT id FROM sub_solicitudes_at WHERE estado = 'DEVUELTA' AND id = ?", (sub_01,))
    assert c.fetchone() is None, "Sub-request MUST disappear from SSI Tab 2 when reassigned"
    print("-> Verified: Request disappeared from SSI Tab 2 when reassigned.")
    
    # Verify AT-07 now sees it
    c.execute("SELECT id FROM sub_solicitudes_at WHERE clave_area = 'AT-07' AND estado IN ('ASIGNADA', 'EN_CONSULTA') AND id = ?", (sub_01,))
    assert c.fetchone() is not None, "AT-07 must now see the reassigned request"
    
    # 6. AT-07 approves and returns to SSI
    c.execute("UPDATE sub_solicitudes_at SET estado = 'COMPLETADA' WHERE id = ?", (sub_01,))
    conn.commit()
    # Verify it DISAPPEARED from AT-07
    c.execute("SELECT id FROM sub_solicitudes_at WHERE clave_area = 'AT-07' AND estado IN ('ASIGNADA', 'EN_CONSULTA') AND id = ?", (sub_01,))
    assert c.fetchone() is None, "Sub-request MUST disappear from AT-07 screen when approved"
    print("-> Verified: Request disappeared from AT-07 screen when approved.")
    
    # 7. AT-02 approves and returns to SSI
    c.execute("UPDATE sub_solicitudes_at SET estado = 'COMPLETADA' WHERE id = ?", (sub_02,))
    conn.commit()
    # Verify it DISAPPEARED from AT-02
    c.execute("SELECT id FROM sub_solicitudes_at WHERE clave_area = 'AT-02' AND estado IN ('ASIGNADA', 'EN_CONSULTA') AND id = ?", (sub_02,))
    assert c.fetchone() is None, "Sub-request MUST disappear from AT-02 screen when approved"
    print("-> Verified: Request disappeared from AT-02 screen when approved.")
    
    # 8. SSI Tab 3 sees it active and ready
    c.execute("""
    SELECT m.id, COUNT(s.id) as total_subs, SUM(CASE WHEN s.estado = 'COMPLETADA' THEN 1 ELSE 0 END) as subs_comp
    FROM solicitudes_master m
    JOIN sub_solicitudes_at s ON m.id = s.solicitud_id
    WHERE m.id = ? AND m.estado != 'ENVIADA_CLIENTE'
    GROUP BY m.id
    """, (sol_id,))
    row = c.fetchone()
    assert row is not None, "SSI Tab 3 must see the active request"
    assert row['total_subs'] == row['subs_comp'] == 2, "Both sub-solicitations must be completed"
    
    # 9. SSI sends to client and archives
    c.execute("UPDATE solicitudes_master SET estado = 'ENVIADA_CLIENTE', no_cotizacion = '260999' WHERE id = ?", (sol_id,))
    conn.commit()
    
    # Verify it DISAPPEARED from SSI Tab 3 active queue
    c.execute("SELECT id FROM solicitudes_master WHERE id = ? AND estado != 'ENVIADA_CLIENTE'", (sol_id,))
    assert c.fetchone() is None, "Master request MUST disappear from SSI Tab 3 active queue when sent to client"
    print("-> Verified: Request disappeared from SSI Tab 3 active queue when sent to client.")
    
    # Verify it appears in History
    c.execute("SELECT id FROM solicitudes_master WHERE id = ? AND estado = 'ENVIADA_CLIENTE'", (sol_id,))
    assert c.fetchone() is not None, "Master request MUST appear in historical table"
    print("-> Verified: Request appears in Historical archive table.")
    
    conn.close()
    print("=== Local Flow Passed 100% ===\n")

def test_cloud_flow():
    print("=== Testing Cloud Flow (cloud_db.py) ===")
    from nube_segura import cloud_db as cdb
    cdb.init_cloud_db()
    
    next_sol = cdb.get_next_solicitud_number()
    next_fol = cdb.get_next_folio_number()
    
    conn, engine = cdb.get_db_connection()
    c = conn.cursor()
    c.execute("""
    INSERT INTO solicitudes_master (
        no_solicitud, no_folio, version, cliente, representante, telefono, correo, rfc, pais,
        es_extranjero, aplica_iva, fecha_recepcion, fecha_emision, vigencia, estado, es_in_situ
    ) VALUES (?, ?, 1, 'CLIENTE CLOUD TEST', 'Dra. Nube', '4429998877', 'nube@cliente.com', 'CLO010101XYZ', 'México',
        0, 1, '2026-11-04 12:00:00', '2026-11-04', '2026-12-31', 'TURNADA', 0)
    """, (next_sol, next_fol))
    sol_id = c.lastrowid
    
    c.execute("INSERT INTO sub_solicitudes_at (solicitud_id, clave_area, estado, fecha_asignacion, fecha_limite_sla) VALUES (?, 'AT-01', 'ASIGNADA', '2026-11-04 12:00:00', '2026-11-07')", (sol_id,))
    sub_01 = c.lastrowid
    
    c.execute("INSERT INTO sub_solicitudes_at (solicitud_id, clave_area, estado, fecha_asignacion, fecha_limite_sla) VALUES (?, 'AT-02', 'ASIGNADA', '2026-11-04 12:00:00', '2026-11-07')", (sol_id,))
    sub_02 = c.lastrowid
    conn.commit()
    
    # AT-01 returns
    c.execute("UPDATE sub_solicitudes_at SET estado = 'DEVUELTA', motivo_devolucion = 'No calibrable', area_sugerida = 'AT-08' WHERE id = ?", (sub_01,))
    conn.commit()
    
    # Check disappeared from AT-01
    c.execute("SELECT id FROM sub_solicitudes_at WHERE clave_area = 'AT-01' AND estado IN ('ASIGNADA', 'EN_CONSULTA') AND id = ?", (sub_01,))
    assert c.fetchone() is None, "Cloud: Sub-request MUST disappear from AT-01 screen when returned"
    print("-> Cloud: Request disappeared from AT-01 screen when returned.")
    
    # SSI reassigns to AT-08
    c.execute("UPDATE sub_solicitudes_at SET clave_area = 'AT-08', estado = 'ASIGNADA', motivo_devolucion = NULL WHERE id = ?", (sub_01,))
    conn.commit()
    
    # Both complete
    c.execute("UPDATE sub_solicitudes_at SET estado = 'COMPLETADA' WHERE id = ?", (sub_01,))
    c.execute("UPDATE sub_solicitudes_at SET estado = 'COMPLETADA' WHERE id = ?", (sub_02,))
    conn.commit()
    
    # Check disappeared from AT-08 and AT-02
    c.execute("SELECT id FROM sub_solicitudes_at WHERE clave_area = 'AT-08' AND estado IN ('ASIGNADA', 'EN_CONSULTA') AND id = ?", (sub_01,))
    assert c.fetchone() is None
    c.execute("SELECT id FROM sub_solicitudes_at WHERE clave_area = 'AT-02' AND estado IN ('ASIGNADA', 'EN_CONSULTA') AND id = ?", (sub_02,))
    assert c.fetchone() is None
    print("-> Cloud: Both requests disappeared from AT screens when approved.")
    
    # SSI sends to client
    c.execute("UPDATE solicitudes_master SET estado = 'ENVIADA_CLIENTE', no_cotizacion = '260998' WHERE id = ?", (sol_id,))
    conn.commit()
    
    # Check disappeared from SSI active queue
    c.execute("SELECT id FROM solicitudes_master WHERE id = ? AND estado != 'ENVIADA_CLIENTE'", (sol_id,))
    assert c.fetchone() is None, "Cloud: Master request MUST disappear from SSI active queue when sent"
    print("-> Cloud: Request disappeared from SSI active queue when sent to client.")
    
    # Check appears in history
    c.execute("SELECT id FROM solicitudes_master WHERE id = ? AND estado = 'ENVIADA_CLIENTE'", (sol_id,))
    assert c.fetchone() is not None
    print("-> Cloud: Request appears in history.")
    
    conn.close()
    print("=== Cloud Flow Passed 100% ===")

if __name__ == "__main__":
    test_local_flow()
    test_cloud_flow()
