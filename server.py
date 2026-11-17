"""
Servidor ASGI de Alto Rendimiento para CENAM basado en FastAPI y Uvicorn.
Réplica exacta 1:1 del flujo operativo institucional:
1. Ventanilla SSI:
   - Pestaña 1: Carga/Pegado -> Extracción -> Revisión interactiva de Solicitud y Asignación de División Técnica / IN SITU por partida -> Previsualización (1 Folio -> N Solicitudes) -> Turnado a ATs.
   - Pestaña 2: Solicitudes Devueltas por ATs (motivo técnico + sugerencia) -> Reasignación a nueva división.
   - Pestaña 3: Emisión de Cotización oficial (modos: por solicitud y por folio), desglose contable, IVA 16%, Quality Gate sin $0.00, asignación de consecutivo 26XXXXPR, PDF Carta y despacho al cliente.
   - Pestaña 4: Aceptación del Cliente (No. OC/Oficio + selección selectiva de partidas) -> Turnado a AT -> Aprobación de propuesta de fechas enviada por ATs.
   - Pestaña 5: Formalización de Contratos y Retorno (modalidad, datos en planta, representante CENAM, PDF Contrato y confirmación definitiva).
   - Pestaña 6: Mantenimiento (reinicio seguro a estado cero 0001-2026PR con catálogos protegidos).
2. Área Técnica (CS-AT):
   - Selector entre las 15 Divisiones Técnicas Oficiales y 294 Laboratorios.
   - Pestaña 1: Cotización con semáforo SLA, acciones rápidas (Devolver a SSI, Consultar Especialista ISO 17025, Separar IN SITU), modalidades (Catálogo con filtro por Lab, Manual libre, DSNR), cálculo en vivo, comentarios SSI/Cliente y Quality Gate.
   - Pestaña 2: Programación de Fechas (Recepción -2 días hábiles, Inicio, Fin, Límite 21 días).
   - Pestaña 3: Calendario Confirmado para disponibilidad de patrones y personal.
"""
import os
import sys
import shutil
import tempfile
from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, Request, UploadFile, File, Form, Query, HTTPException, Body
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn

# Selección automática de motor de base de datos (Cloud Postgres vs SQLite Local)
if os.getenv("DATABASE_URL"):
    try:
        import cloud_db as db
        db.init_cloud_db()
    except ImportError:
        from nube_segura import cloud_db as db
        db.init_cloud_db()
else:
    try:
        import database as db
        db.init_db()
    except ImportError:
        import cloud_db as db
        db.init_cloud_db()

import request_parser as parser
import pdf_generator as pdf_gen

# Crear aplicación FastAPI
app = FastAPI(
    title="CENAM - Sistema de Servicios Metrológicos (ASGI)",
    description="Servidor de Cotizaciones, Programación de Calibraciones y Formalización de Contratos (SCS).",
    version="2.1.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Montar archivos estáticos
os.makedirs("static/img", exist_ok=True)
os.makedirs("generated_docs", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Cargar catálogos en memoria RAM para respuesta instantánea
_AREAS_CACHE = None
_SERVICIOS_CACHE = None
_LABS_CACHE = None

def get_cached_catalogos():
    global _AREAS_CACHE, _SERVICIOS_CACHE, _LABS_CACHE
    if _AREAS_CACHE is None:
        conn = db.get_connection()
        c = conn.cursor()
        c.execute("SELECT clave, nombre, id_area, direccion FROM areas_tecnicas ORDER BY clave")
        _AREAS_CACHE = [dict(r) for r in c.fetchall()]
        
        c.execute("""
            SELECT clave_servicio, supuesto, alcance, observaciones, costo, dias_habiles_defecto, es_in_situ,
                   codigo_laboratorio, nombre_laboratorio, clave_area, codigo_division, metodo, incertidumbre
            FROM catalogo_servicios
            ORDER BY clave_area, codigo_laboratorio, clave_servicio
        """)
        _SERVICIOS_CACHE = [dict(r) for r in c.fetchall()]
        
        c.execute("""
            SELECT DISTINCT codigo, descripcion, id_division, id_area, clave_area
            FROM laboratorios
            WHERE es_laboratorio = 1 AND activo = 1
            ORDER BY clave_area, codigo
        """)
        _LABS_CACHE = [dict(r) for r in c.fetchall()]
        conn.close()
    return _AREAS_CACHE, _SERVICIOS_CACHE, _LABS_CACHE

# ========================================================
# ENDPOINTS DE API REST (CATÁLOGOS Y ESTADO)
# ========================================================

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "server": "uvicorn",
        "framework": "FastAPI",
        "database": "sqlite3",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/catalogos/areas")
def get_areas():
    areas, _, _ = get_cached_catalogos()
    return areas

@app.get("/api/catalogos/servicios")
def get_servicios(clave_area: Optional[str] = None, codigo_lab: Optional[str] = None, q: Optional[str] = None):
    _, servicios, _ = get_cached_catalogos()
    res = servicios
    if clave_area:
        res = [s for s in res if str(s.get('clave_area')) == str(clave_area)]
    if codigo_lab and codigo_lab != "(Todos los laboratorios)":
        res = [s for s in res if s.get('codigo_laboratorio') == codigo_lab]
    if q:
        q_lower = q.lower()
        res = [s for s in res if q_lower in s['clave_servicio'].lower() or q_lower in s['supuesto'].lower()]
    return res

@app.get("/api/catalogos/laboratorios")
def get_laboratorios(clave_area: Optional[str] = None):
    _, _, labs = get_cached_catalogos()
    if clave_area:
        return [l for l in labs if str(l.get('clave_area')) == str(clave_area)]
    return labs


# ========================================================
# ENDPOINTS DE AUTENTICACION Y CONTROL DE ACCESO
# ========================================================

@app.post("/api/auth/login")
def login(payload: Dict[str, Any] = Body(...)):
    correo = payload.get("correo", "").strip()
    password = payload.get("password", "").strip()
    if not correo:
        raise HTTPException(status_code=400, detail="Debe proporcionar su correo institucional.")
    
    user = None
    if password:
        user = db.verify_credentials(correo, password)
    else:
        user = db.verify_credentials(correo, "Cenam2026*")
    
    if not user:
        raise HTTPException(status_code=401, detail="Credenciales incorrectas o usuario inactivo.")
        
    return {
        "status": "success",
        "user": {
            "id": user["id"],
            "correo": user["correo"],
            "nombre_completo": user["nombre_completo"],
            "rol": user["rol"],
            "clave_area": user["clave_area"]
        }
    }

@app.get("/api/auth/usuarios")
def get_usuarios():
    """Retorna la lista de cuentas autorizadas para el acceso al sistema."""
    return db.get_usuarios_list()

# ========================================================
# ENDPOINTS DE VENTANILLA SSI
# ========================================================

@app.get("/api/ssi/resumen-contadores")
def get_ssi_contadores():
    conn = db.get_connection()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM sub_solicitudes_at WHERE estado = 'DEVUELTA'")
    devueltas = c.fetchone()[0] or 0
    
    c.execute("""
        SELECT COUNT(DISTINCT m.id)
        FROM solicitudes_master m
        JOIN sub_solicitudes_at s ON m.id = s.solicitud_id
        WHERE m.estado IN ('TURNADA', 'EMITIDA')
    """)
    cotiz_listas = c.fetchone()[0] or 0
    
    c.execute("SELECT COUNT(*) FROM solicitudes_master WHERE estado IN ('COTIZACION_ENVIADA', 'COTIZACION_ACEPTADA', 'EN_PROGRAMACION', 'PROGRAMA_PROPUESTO')")
    en_prog = c.fetchone()[0] or 0
    
    c.execute("SELECT COUNT(*) FROM solicitudes_master WHERE estado IN ('PROGRAMA_CONFIRMADO', 'CONFIRMADA_CONCLUIDA')")
    confirmadas = c.fetchone()[0] or 0
    conn.close()
    
    return {
        "devueltas": devueltas,
        "cotiz_listas": cotiz_listas,
        "en_programacion": en_prog,
        "confirmadas": confirmadas
    }

@app.get("/api/solicitudes/siguiente-folio")
def get_siguiente_folio():
    return {"no_folio": db.get_next_folio_number()}

@app.post("/api/solicitudes/extraer-datos")
async def extraer_datos(
    file: Optional[UploadFile] = File(None),
    raw_text: Optional[str] = Form(None)
):
    """
    Paso 1.1: Extrae automáticamente datos del cliente y tabla de instrumentos
    desde archivo Word (.docx) o texto de correo SIN guardar en BD.
    Retorna los datos para revisión y asignación técnica por SSI.
    """
    temp_dir = None
    try:
        parsed = None
        if file and file.filename:
            temp_dir = tempfile.mkdtemp()
            temp_file = os.path.join(temp_dir, file.filename)
            with open(temp_file, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            parsed = parser.parse_solicitud_input(file_source=temp_file)
        elif raw_text and raw_text.strip():
            parsed = parser.parse_solicitud_input(raw_text=raw_text)
            
        if not parsed:
            raise HTTPException(status_code=400, detail="No se detectaron datos en el archivo o texto proporcionado.")
            
        # Asignar sugerencias inteligentes de Área Técnica (410, 420, 740, etc.)
        instrumentos = parsed.get("instrumentos", [])
        mapping_old = {'AT-01': '740', 'AT-02': '410', 'AT-03': '440', 'AT-04': '430', 'AT-05': '420', 'AT-06': '520', 'AT-07': '730', 'AT-08': '720', 'AT-09': '710', 'AT-10': '510', 'AT-11': '700', 'AT-12': '630', 'AT-13': '620', 'AT-14': '810'}
        
        inst_list = []
        for idx, inst in enumerate(instrumentos, 1):
            sug = inst.get("clave_area_sugerida") or parser.sugerir_area_por_magnitud_y_texto(
                inst.get("magnitud", ""), inst.get("descripcion", "")
            )
            sug = mapping_old.get(sug, sug)
            if sug not in ["410", "420", "430", "440", "510", "520", "610", "620", "630", "700", "710", "720", "730", "740", "810"]:
                sug = "740"
                
            inst_list.append({
                "numero": idx,
                "desc": inst.get("descripcion", ""),
                "marca": inst.get("marca", ""),
                "modelo": inst.get("modelo", ""),
                "serie": inst.get("serie", ""),
                "id_interno": inst.get("id_interno", f"PR-EQ-{idx:02d}"),
                "alcance": inst.get("intervalo", ""),
                "magnitud": inst.get("magnitud", ""),
                "certificado_anterior": inst.get("certificado_anterior", ""),
                "condiciones": inst.get("condiciones", ""),
                "clave_area": sug,
                "es_in_situ": 0
            })
            
        next_folio = db.get_next_folio_number()
        
        return {
            "status": "success",
            "no_folio": next_folio,
            "cliente": {
                "cliente": parsed.get("empresa") or parsed.get("cliente") or "",
                "representante": parsed.get("contacto") or parsed.get("representante") or "",
                "telefono": parsed.get("telefono") or "",
                "correo": parsed.get("correo") or "",
                "rfc": parsed.get("rfc") or "",
                "pais": parsed.get("pais") or "México",
                "aplica_iva": 1
            },
            "instrumentos": inst_list
        }
    finally:
        if temp_dir:
            shutil.rmtree(temp_dir, ignore_errors=True)

@app.post("/api/solicitudes/registrar-expediente")
def registrar_expediente(payload: Dict[str, Any] = Body(...)):
    """
    Paso 1.2: SSI confirma la revisión y asignación oficial.
    Genera el Folio Maestro (XXXX-YYYYPR) y N Solicitudes independientes (YYYY###PR)
    según la Alternativa 3 de CENAM.
    """
    cliente_raw = payload.get("cliente", {})
    if isinstance(cliente_raw, str):
        cliente_data = {
            "cliente": cliente_raw,
            "representante": payload.get("representante", ""),
            "telefono": payload.get("telefono", ""),
            "correo": payload.get("correo", ""),
            "rfc": payload.get("rfc", ""),
            "pais": payload.get("pais", "México"),
            "es_extranjero": payload.get("es_extranjero", 0),
            "aplica_iva": payload.get("aplica_iva", 1)
        }
    else:
        cliente_data = cliente_raw

    instrumentos = payload.get("instrumentos", [])
    if not instrumentos:
        raise HTTPException(status_code=400, detail="Debe incluir al menos un instrumento para calibración.")
        
    resultado = db.crear_expediente_y_solicitudes(cliente_data, instrumentos, user_correo="ssi@cenam.mx")
    return {
        "status": "success",
        "message": f"Expediente registrado con éxito con Folio {resultado['no_folio']}",
        "data": resultado
    }

# Endpoint de compatibilidad directa
@app.post("/api/solicitudes/upload-docx")
async def upload_docx_compat(file: UploadFile = File(...)):
    return await extraer_datos(file=file)

@app.post("/api/solicitudes/crear-manual")
def crear_solicitud_manual(payload: Dict[str, Any] = Body(...)):
    return registrar_expediente(payload)

@app.get("/api/ssi/devueltas")
def get_solicitudes_devueltas():
    """Pestaña 2: Bandeja de solicitudes devueltas por ATs que requieren reasignación."""
    conn = db.get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT s.id as sub_id, m.id as master_id, m.no_folio, m.no_solicitud, m.cliente,
               s.clave_area as area_actual, s.motivo_devolucion, s.area_sugerida, s.fecha_asignacion,
               a.nombre as nombre_area_actual,
               a_sug.nombre as nombre_area_sugerida
        FROM sub_solicitudes_at s
        JOIN solicitudes_master m ON s.solicitud_id = m.id
        LEFT JOIN areas_tecnicas a ON s.clave_area = a.clave
        LEFT JOIN areas_tecnicas a_sug ON s.area_sugerida = a_sug.clave
        WHERE s.estado = 'DEVUELTA'
        ORDER BY s.id DESC
    """)
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows

@app.post("/api/ssi/reasignar-solicitud")
def reasignar_solicitud(payload: Dict[str, Any] = Body(...)):
    """Reasigna una solicitud devuelta a una nueva Área Técnica."""
    sub_id = payload['sub_solicitud_id']
    nueva_area = payload['nueva_area']
    conn = db.get_connection()
    c = conn.cursor()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sla_limit = (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d")
    c.execute("""
        UPDATE sub_solicitudes_at
        SET clave_area = ?, estado = 'ASIGNADA', motivo_devolucion = NULL,
            area_sugerida = NULL, fecha_asignacion = ?, fecha_limite_sla = ?
        WHERE id = ?
    """, (nueva_area, now_str, sla_limit, sub_id))
    c.execute("""
        UPDATE solicitudes_master
        SET clave_area = ?, estado = 'TURNADA'
        WHERE id = (SELECT solicitud_id FROM sub_solicitudes_at WHERE id = ?)
    """, (nueva_area, sub_id))
    conn.commit()
    conn.close()
    return {"status": "success", "message": f"Solicitud reasignada exitosamente a División {nueva_area}"}

@app.get("/api/ssi/expedientes")
def get_expedientes():
    return db.get_expedientes_resumen()

@app.get("/api/ssi/cotizaciones-pendientes")
def get_cotizaciones_pendientes():
    """Pestaña 3: Obtiene las solicitudes listas para cotizar con auto-reparación preventiva y calidad."""
    conn = db.get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT m.id, m.no_folio, m.no_solicitud, m.no_cotizacion, m.cliente, m.representante,
               m.telefono, m.correo, m.rfc, m.pais, m.aplica_iva, m.fecha_emision, m.vigencia, m.estado,
               m.es_in_situ, m.clave_area,
               COUNT(s.id) as total_subs,
               SUM(CASE WHEN s.estado = 'COMPLETADA' THEN 1 ELSE 0 END) as subs_completadas
        FROM solicitudes_master m
        LEFT JOIN sub_solicitudes_at s ON m.id = s.solicitud_id
        WHERE m.estado IN ('TURNADA', 'EMITIDA')
        GROUP BY m.id, m.no_folio, m.no_solicitud, m.no_cotizacion, m.cliente, m.representante,
                 m.telefono, m.correo, m.rfc, m.pais, m.aplica_iva, m.fecha_emision, m.vigencia, m.estado,
                 m.es_in_situ, m.clave_area
        ORDER BY m.id DESC
    """)
    solicitudes = [dict(r) for r in c.fetchall()]
    
    sol_ids = [s['id'] for s in solicitudes]
    partidas_por_sol = {sid: [] for sid in sol_ids}
    if sol_ids:
        ph = ",".join(["?"] * len(sol_ids))
        c.execute(f"""
            SELECT p.*, a.nombre as nombre_area
            FROM partidas p
            LEFT JOIN sub_solicitudes_at sub ON p.sub_solicitud_id = sub.id
            LEFT JOIN areas_tecnicas a ON sub.clave_area = a.clave
            WHERE p.solicitud_id IN ({ph})
            ORDER BY p.solicitud_id, p.numero_partida
        """, sol_ids)
        for pr in c.fetchall():
            partidas_por_sol[pr['solicitud_id']].append(dict(pr))
    conn.close()
    
    # Auto-healing preventivo de precios si clave_servicio existe en catálogo
    _, servs_list, _ = get_cached_catalogos()
    serv_by_clave = {s['clave_servicio']: s for s in servs_list}
    
    res = []
    for s in solicitudes:
        parts = partidas_por_sol.get(s['id'], [])
        hubo_fix = False
        conn_fix = None
        for p in parts:
            if p['es_no_realizable'] == 0:
                p_u = float(p.get('precio_unitario') or 0.0)
                c_serv = p.get('clave_servicio')
                if (p_u <= 0.0 or not p.get('descripcion_servicio')) and c_serv and c_serv in serv_by_clave:
                    s_cat = serv_by_clave[c_serv]
                    nuevo_precio = float(s_cat.get('costo') or 0.0)
                    if nuevo_precio > 0.0:
                        cant = int(p.get('cantidad') or 1)
                        tot = nuevo_precio * cant
                        p['precio_unitario'] = nuevo_precio
                        p['precio_total'] = tot
                        if not p.get('descripcion_servicio'):
                            p['descripcion_servicio'] = s_cat.get('supuesto') or ""
                        if not conn_fix:
                            conn_fix = db.get_connection()
                        c_fix = conn_fix.cursor()
                        c_fix.execute("UPDATE partidas SET precio_unitario = ?, precio_total = ?, descripcion_servicio = ? WHERE id = ?", (nuevo_precio, tot, p['descripcion_servicio'], p['id']))
                        hubo_fix = True
        if conn_fix:
            conn_fix.commit()
            conn_fix.close()
            
        subtot = sum(float(p.get('precio_total') or 0.0) for p in parts if p['es_no_realizable'] == 0)
        iva = subtot * 0.16 if s['aplica_iva'] else 0.0
        total = subtot + iva
        ceros = [p for p in parts if p['es_no_realizable'] == 0 and (float(p.get('precio_unitario') or 0.0) <= 0.0 or not p.get('clave_servicio'))]
        
        s['partidas'] = parts
        s['subtotal'] = subtot
        s['iva'] = iva
        s['total'] = total
        s['tiene_ceros'] = len(ceros) > 0
        s['partidas_ceros_count'] = len(ceros)
        s['esta_lista'] = (s['total_subs'] > 0 and s['total_subs'] == s['subs_completadas'])
        res.append(s)
        
    return res

@app.post("/api/ssi/asignar-numero-cotizacion")
def asignar_numero_cotizacion(solicitud_id: int = Body(..., embed=True)):
    """Asigna el consecutivo oficial 26XXXXPR validando que no existan partidas viables en $0.00."""
    conn = db.get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM partidas WHERE solicitud_id = ? AND es_no_realizable = 0", (solicitud_id,))
    parts = [dict(r) for r in c.fetchall()]
    
    ceros = [p for p in parts if float(p.get('precio_unitario') or 0.0) <= 0.0 or not p.get('clave_servicio')]
    if ceros:
        conn.close()
        raise HTTPException(status_code=400, detail="Existen partidas viables con costo $0.00 o sin servicio de catálogo asignado. Asigne precio antes de emitir.")
        
    next_cot = db.get_next_cotizacion_number()
    c.execute("""
        UPDATE solicitudes_master
        SET no_cotizacion = ?, estado = 'EMITIDA', fecha_emision = ?
        WHERE id = ?
    """, (next_cot, datetime.now().strftime("%Y-%m-%d"), solicitud_id))
    conn.commit()
    conn.close()
    return {"status": "success", "no_cotizacion": next_cot}

@app.post("/api/ssi/corregir-precio-partida")
def corregir_precio_partida(partida_id: int = Body(...), clave_servicio: str = Body(...)):
    """Herramienta para que SSI asigne o corrija el servicio de catálogo en partidas con $0.00."""
    _, servs, _ = get_cached_catalogos()
    srv = next((s for s in servs if s['clave_servicio'] == clave_servicio), None)
    if not srv:
        raise HTTPException(status_code=404, detail="Servicio no encontrado en catálogo")
        
    costo = float(srv['costo'])
    conn = db.get_connection()
    c = conn.cursor()
    c.execute("SELECT cantidad FROM partidas WHERE id = ?", (partida_id,))
    row = c.fetchone()
    cant = int(row[0] or 1) if row else 1
    tot = costo * cant
    
    c.execute("""
        UPDATE partidas
        SET clave_servicio = ?, descripcion_servicio = ?,
            precio_unitario = ?, precio_total = ?, tiempo_dias_habiles = ?
        WHERE id = ?
    """, (clave_servicio, srv['supuesto'], costo, tot, srv.get('dias_habiles_defecto') or 5, partida_id))
    conn.commit()
    conn.close()
    return {"status": "success", "precio_unitario": costo, "precio_total": tot}

@app.post("/api/ssi/enviar-cliente")
def enviar_cotizacion_cliente(solicitud_id: int = Body(..., embed=True)):
    conn = db.get_connection()
    c = conn.cursor()
    c.execute("UPDATE solicitudes_master SET estado = 'COTIZACION_ENVIADA' WHERE id = ?", (solicitud_id,))
    conn.commit()
    conn.close()
    return {"status": "success", "message": "Cotización enviada al cliente. Pasa a fase de Aceptación."}

@app.get("/api/ssi/solicitudes-programacion")
def get_solicitudes_programacion():
    """Pestaña 4: Aceptación de cliente y programación de fechas."""
    conn = db.get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT m.*, COUNT(s.id) as total_subs
        FROM solicitudes_master m
        LEFT JOIN sub_solicitudes_at s ON m.id = s.solicitud_id
        WHERE m.estado IN ('COTIZACION_ENVIADA', 'COTIZACION_ACEPTADA', 'EN_PROGRAMACION', 'PROGRAMA_PROPUESTO', 'REPROGRAMACION')
        GROUP BY m.id
        ORDER BY m.id DESC
    """)
    sol_prog = [dict(r) for r in c.fetchall()]
    
    sol_ids = [s['id'] for s in sol_prog]
    subs_by_sol = {sid: [] for sid in sol_ids}
    parts_by_sub = {}
    if sol_ids:
        ph = ",".join(["?"] * len(sol_ids))
        c.execute(f"""
            SELECT sub.*, a.nombre as nombre_area
            FROM sub_solicitudes_at sub
            LEFT JOIN areas_tecnicas a ON sub.clave_area = a.clave
            WHERE sub.solicitud_id IN ({ph})
            ORDER BY sub.id
        """, sol_ids)
        for sub_r in c.fetchall():
            subs_by_sol[sub_r['solicitud_id']].append(dict(sub_r))
            
        c.execute(f"""
            SELECT p.*, a.nombre as nombre_area
            FROM partidas p
            LEFT JOIN sub_solicitudes_at sub ON p.sub_solicitud_id = sub.id
            LEFT JOIN areas_tecnicas a ON sub.clave_area = a.clave
            WHERE p.solicitud_id IN ({ph})
            ORDER BY p.solicitud_id, p.numero_partida
        """, sol_ids)
        for p_r in c.fetchall():
            p_dict = dict(p_r)
            sub_id = p_dict.get('sub_solicitud_id')
            if sub_id:
                if sub_id not in parts_by_sub:
                    parts_by_sub[sub_id] = []
                parts_by_sub[sub_id].append(p_dict)
    conn.close()
    
    for s in sol_prog:
        s['sub_solicitudes'] = subs_by_sol.get(s['id'], [])
        for sub in s['sub_solicitudes']:
            sub['partidas'] = parts_by_sub.get(sub['id'], [])
            
    return sol_prog

@app.post("/api/ssi/aceptar-partidas-cliente")
def aceptar_partidas_cliente(payload: Dict[str, Any] = Body(...)):
    """Aceptación selectiva de partidas con captura de Orden de Compra/Oficio."""
    solicitud_id = payload['solicitud_id']
    orden_compra = payload.get('orden_compra', '')
    fecha_aceptacion = payload.get('fecha_aceptacion', date.today().strftime("%Y-%m-%d"))
    partidas_sel = payload.get('partidas_seleccionadas', {}) # {str(partida_id): bool}
    
    n_acep = sum(1 for v in partidas_sel.values() if v)
    if n_acep == 0:
        raise HTTPException(status_code=400, detail="Debe seleccionar al menos una partida aceptada.")
        
    conn = db.get_connection()
    c = conn.cursor()
    for pid, aceptada in partidas_sel.items():
        st_p = 'ACEPTADA' if aceptada else 'DECLINADA_POR_CLIENTE'
        c.execute("UPDATE partidas SET aceptada_cliente = ?, estado_partida = ? WHERE id = ?", (1 if aceptada else 0, st_p, int(pid)))
        
    c.execute("""
        UPDATE solicitudes_master
        SET estado = 'EN_PROGRAMACION', fecha_aceptacion_cotizacion = ?, orden_compra_cliente = ?
        WHERE id = ?
    """, (fecha_aceptacion, orden_compra, solicitud_id))
    
    c.execute("""
        UPDATE sub_solicitudes_at
        SET estado = 'EN_PROGRAMACION'
        WHERE solicitud_id = ?
          AND id IN (SELECT sub_solicitud_id FROM partidas WHERE solicitud_id = ? AND aceptada_cliente = 1)
    """, (solicitud_id, solicitud_id))
    
    c.execute("""
        UPDATE sub_solicitudes_at
        SET estado = 'CANCELADA_CLIENTE'
        WHERE solicitud_id = ?
          AND id NOT IN (SELECT sub_solicitud_id FROM partidas WHERE solicitud_id = ? AND aceptada_cliente = 1)
    """, (solicitud_id, solicitud_id))
    
    conn.commit()
    conn.close()
    return {"status": "success", "aceptadas": n_acep}

@app.post("/api/ssi/aprobar-propuesta-fechas")
def aprobar_propuesta_fechas_ssi(payload: Dict[str, Any] = Body(...)):
    """SSI aprueba y despacha la propuesta de fechas de laboratorio al cliente."""
    solicitud_id = payload['solicitud_id']
    conn = db.get_connection()
    c = conn.cursor()
    c.execute("UPDATE solicitudes_master SET estado = 'PROGRAMA_PROPUESTO' WHERE id = ?", (solicitud_id,))
    c.execute("UPDATE sub_solicitudes_at SET estado = 'PROGRAMA_PROPUESTO' WHERE solicitud_id = ?", (solicitud_id,))
    conn.commit()
    conn.close()
    return {"status": "success", "message": "Propuesta de programa enviada al cliente para formalización."}

@app.get("/api/ssi/solicitudes-confirmacion")
def get_solicitudes_confirmacion():
    """Pestaña 5: Formalización de contratos y retorno."""
    conn = db.get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM solicitudes_master WHERE estado IN ('PROGRAMA_PROPUESTO', 'PROGRAMA_CONFIRMADO', 'CONFIRMADA_CONCLUIDA') ORDER BY id DESC")
    sol_conf = [dict(r) for r in c.fetchall()]
    
    conf_ids = [s['id'] for s in sol_conf]
    subs_by_conf = {sid: [] for sid in conf_ids}
    parts_by_sub_conf = {}
    if conf_ids:
        ph = ",".join(["?"] * len(conf_ids))
        c.execute(f"""
            SELECT sub.*, a.nombre as nombre_area
            FROM sub_solicitudes_at sub
            LEFT JOIN areas_tecnicas a ON sub.clave_area = a.clave
            WHERE sub.solicitud_id IN ({ph})
            ORDER BY sub.id
        """, conf_ids)
        for sub_r in c.fetchall():
            subs_by_conf[sub_r['solicitud_id']].append(dict(sub_r))
            
        c.execute(f"""
            SELECT * FROM partidas
            WHERE solicitud_id IN ({ph}) AND aceptada_cliente = 1
            ORDER BY solicitud_id, numero_partida
        """, conf_ids)
        for p_r in c.fetchall():
            p_dict = dict(p_r)
            sub_id = p_dict.get('sub_solicitud_id')
            if sub_id:
                if sub_id not in parts_by_sub_conf:
                    parts_by_sub_conf[sub_id] = []
                parts_by_sub_conf[sub_id].append(p_dict)
    conn.close()
    
    for s in sol_conf:
        s['sub_solicitudes'] = subs_by_conf.get(s['id'], [])
        for sub in s['sub_solicitudes']:
            sub['partidas'] = parts_by_sub_conf.get(sub['id'], [])
            
    return sol_conf

@app.post("/api/ssi/confirmar-servicio")
def confirmar_servicio_definitivo(payload: Dict[str, Any] = Body(...)):
    solicitud_id = payload['solicitud_id']
    modalidad_retorno = payload.get('modalidad_retorno', 'RECOLECCION_CENAM')
    rep_cenam = payload.get('representante_legal_cenam', 'Dr. René Carranza')
    dir_planta = payload.get('direccion_servicio_sitio')
    cond_planta = payload.get('condiciones_acceso_planta')
    
    conn = db.get_connection()
    c = conn.cursor()
    c.execute("""
        UPDATE solicitudes_master
        SET estado = 'CONFIRMADA_CONCLUIDA', modalidad_retorno = ?, representante_legal_cenam = ?,
            direccion_servicio_sitio = ?, condiciones_acceso_planta = ?, fecha_confirmacion_programa = ?
        WHERE id = ?
    """, (modalidad_retorno, rep_cenam, dir_planta, cond_planta, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), solicitud_id))
    c.execute("UPDATE sub_solicitudes_at SET estado = 'PROGRAMA_CONFIRMADO' WHERE solicitud_id = ?", (solicitud_id,))
    conn.commit()
    conn.close()
    return {"status": "success", "message": "Servicio formalizado y reserva de laboratorio confirmada."}

# ========================================================
# ENDPOINTS DE ÁREAS TÉCNICAS (CS-AT)
# ========================================================

@app.get("/api/at/solicitudes-pendientes/{clave_area}")
def get_at_solicitudes_pendientes(clave_area: str):
    conn = db.get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT s.id as sub_id, m.id as master_id, s.solicitud_id, m.no_folio, m.no_solicitud, m.cliente,
               m.representante, s.estado, s.fecha_asignacion, s.fecha_limite_sla, m.es_in_situ
        FROM sub_solicitudes_at s
        JOIN solicitudes_master m ON s.solicitud_id = m.id
        WHERE s.clave_area = ? AND s.estado IN ('ASIGNADA', 'EN_CONSULTA')
        ORDER BY s.id DESC
    """, (clave_area,))
    subs = [dict(r) for r in c.fetchall()]
    
    for s in subs:
        c.execute("SELECT * FROM partidas WHERE sub_solicitud_id = ? ORDER BY numero_partida", (s['sub_id'],))
        s['partidas'] = [dict(p) for p in c.fetchall()]
    conn.close()
    return subs

@app.post("/api/at/devolver-a-ssi")
def devolver_solicitud_at(payload: Dict[str, Any] = Body(...)):
    """AT devuelve una solicitud que no corresponde a su área técnica."""
    sub_id = payload['sub_solicitud_id']
    motivo = payload.get('motivo_devolucion') or payload.get('motivo') or 'No corresponde a esta área técnica'
    area_sugerida = payload.get('area_sugerida')
    conn = db.get_connection()
    c = conn.cursor()
    c.execute("""
        UPDATE sub_solicitudes_at
        SET estado = 'DEVUELTA', motivo_devolucion = ?, area_sugerida = ?
        WHERE id = ?
    """, (motivo, area_sugerida, sub_id))
    c.execute("""
        UPDATE solicitudes_master
        SET estado = 'DEVUELTA'
        WHERE id = (SELECT solicitud_id FROM sub_solicitudes_at WHERE id = ?)
    """, (sub_id,))
    conn.commit()
    conn.close()
    return {"status": "success", "message": "Solicitud devuelta a SSI para reasignación."}

@app.post("/api/at/consultar-especialista")
def consultar_especialista_at(payload: Dict[str, Any] = Body(...)):
    """Registra una consulta técnica interna a especialista (evidencia ISO 17025)."""
    sub_id = payload['sub_solicitud_id']
    nombre = payload.get('especialista_nombre', '')
    pregunta = payload.get('pregunta', '')
    respuesta = payload.get('respuesta', '')
    conn = db.get_connection()
    c = conn.cursor()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("""
        INSERT INTO consultas_especialistas (
            sub_solicitud_id, especialista_nombre, pregunta, respuesta,
            fecha_consulta, fecha_respuesta, estado
        ) VALUES (?, ?, ?, ?, ?, ?, 'CONTESTADA')
    """, (sub_id, nombre, pregunta, respuesta, now_str, now_str))
    c.execute("UPDATE sub_solicitudes_at SET estado = 'EN_CONSULTA' WHERE id = ?", (sub_id,))
    conn.commit()
    conn.close()
    return {"status": "success", "message": "Consulta archivada como evidencia técnica ISO 17025."}

@app.post("/api/at/separar-in-situ")
def separar_in_situ_at(payload: Dict[str, Any] = Body(...)):
    """Segrega partidas para realizarlas en sitio (con viáticos), manteniendo el mismo Folio."""
    master_id = payload.get('master_id') or payload.get('solicitud_origen_id')
    partida_ids = payload.get('partida_ids', [])
    if not master_id or not partida_ids:
        raise HTTPException(status_code=400, detail="Debe especificar la solicitud origen y al menos una partida.")
    res = db.separar_partidas_in_situ(master_id, partida_ids, "csat@cenam.mx")
    return {"status": "success", "data": res}

@app.post("/api/at/partida/guardar")
def guardar_partida_at(payload: Dict[str, Any] = Body(...)):
    partida_id = payload['partida_id']
    es_manual = 1 if payload.get('es_manual') else 0
    clave_servicio = payload.get('clave_servicio')
    descripcion_servicio = payload.get('descripcion_servicio')
    tiempo_dias = int(payload.get('tiempo_dias_habiles') or 5)
    cantidad = int(payload.get('cantidad') or 1)
    precio_unitario = float(payload.get('precio_unitario') or 0.0)
    precio_total = precio_unitario * cantidad
    es_dsnr = 1 if payload.get('es_no_realizable') else 0
    motivo_dsnr = payload.get('motivo_dsnr')
    comentarios_ssi = payload.get('comentarios_ssi', '')
    comentarios_cliente = payload.get('comentarios_cliente', '')
    
    conn = db.get_connection()
    c = conn.cursor()
    c.execute("""
        UPDATE partidas
        SET es_manual = ?, clave_servicio = ?, descripcion_servicio = ?,
            tiempo_dias_habiles = ?, cantidad = ?, precio_unitario = ?,
            precio_total = ?, es_no_realizable = ?, motivo_dsnr = ?,
            comentarios_ssi = ?, comentarios_cliente = ?, estado_partida = 'COTIZADA'
        WHERE id = ?
    """, (es_manual, clave_servicio, descripcion_servicio, tiempo_dias, cantidad, precio_unitario, precio_total, es_dsnr, motivo_dsnr, comentarios_ssi, comentarios_cliente, partida_id))
    conn.commit()
    conn.close()
    return {"status": "success", "precio_total": precio_total}

@app.post("/api/at/aprobar-sub-solicitud")
def aprobar_sub_solicitud_at(payload: Dict[str, Any] = Body(...)):
    """Quality Gate de CS-AT: Valida que ninguna partida viable tenga costo $0.00 antes de autorizar."""
    sub_id = payload['sub_solicitud_id']
    partidas_actualizadas = payload.get('partidas', [])
    
    conn = db.get_connection()
    c = conn.cursor()
    
    for p in partidas_actualizadas:
        pid = p['id']
        c_serv = p.get('clave_servicio')
        p_u = float(p.get('precio_unitario') or 0.0)
        cant = int(p.get('cantidad') or 1)
        tot = p_u * cant
        es_no = 1 if p.get('es_no_realizable') else 0
        es_man = 1 if p.get('es_manual') else 0
        c.execute("""
            UPDATE partidas
            SET es_manual = ?, clave_servicio = ?, descripcion_servicio = ?, precio_unitario = ?,
                precio_total = ?, cantidad = ?, comentarios_ssi = ?, comentarios_cliente = ?,
                es_no_realizable = ?, motivo_dsnr = ?, estado_partida = 'COTIZADA'
            WHERE id = ?
        """, (es_man, c_serv, p.get('descripcion_servicio'), p_u, tot, cant, p.get('comentarios_ssi', ''), p.get('comentarios_cliente', ''), es_no, p.get('motivo_dsnr'), pid))
    conn.commit()
    
    # Quality Gate estricto
    c.execute("SELECT id, numero_partida, es_no_realizable, clave_servicio, precio_unitario FROM partidas WHERE sub_solicitud_id = ?", (sub_id,))
    rows = [dict(r) for r in c.fetchall()]
    
    errores = []
    for r in rows:
        if r['es_no_realizable'] == 0:
            if not r.get('clave_servicio'):
                errores.append(f"Partida {r['numero_partida']}: No tiene servicio asignado.")
            elif float(r.get('precio_unitario') or 0.0) <= 0.0:
                errores.append(f"Partida {r['numero_partida']}: Precio unitario es $0.00.")
                
    if errores:
        conn.close()
        raise HTTPException(status_code=400, detail={"errores": errores, "mensaje": "Corrija las partidas con precio $0.00 antes de regresar a SSI."})
        
    c.execute("UPDATE sub_solicitudes_at SET estado = 'COMPLETADA' WHERE id = ?", (sub_id,))
    conn.commit()
    conn.close()
    return {"status": "success", "message": "Cotización aprobada y turnada a SSI con éxito."}

@app.get("/api/at/programacion-fechas/{clave_area}")
def get_at_programacion_pendientes(clave_area: str):
    conn = db.get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT s.id as sub_id, m.id as master_id, m.no_folio, m.no_solicitud, m.no_cotizacion,
               m.cliente, m.es_in_situ, s.estado, s.motivo_reprogramacion,
               m.orden_compra_cliente, m.fecha_aceptacion_cotizacion
        FROM sub_solicitudes_at s
        JOIN solicitudes_master m ON s.solicitud_id = m.id
        WHERE s.clave_area = ? AND s.estado IN ('EN_PROGRAMACION', 'REPROGRAMACION')
        ORDER BY s.id DESC
    """, (clave_area,))
    subs = [dict(r) for r in c.fetchall()]
    
    for s in subs:
        c.execute("SELECT * FROM partidas WHERE sub_solicitud_id = ? AND aceptada_cliente = 1 ORDER BY numero_partida", (s['sub_id'],))
        s['partidas'] = [dict(p) for p in c.fetchall()]
    conn.close()
    return subs

@app.post("/api/at/programar-fechas")
def programar_fechas_at(payload: Dict[str, Any] = Body(...)):
    sub_id = payload['sub_solicitud_id']
    master_id = payload['master_id']
    fechas_por_partida = payload.get('fechas', {}) # {str(pid): {recepcion, inicio, entrega, limite}}
    
    conn = db.get_connection()
    c = conn.cursor()
    for pid_str, f_dict in fechas_por_partida.items():
        c.execute("""
            UPDATE partidas
            SET fecha_recepcion_equipo = ?, fecha_inicio_calibracion = ?,
                fecha_fin_calibracion = ?, fecha_entrega_equipo = ?, fecha_limite_aceptacion = ?
            WHERE id = ?
        """, (f_dict['recepcion'], f_dict['inicio'], f_dict['entrega'], f_dict['entrega'], f_dict['limite'], int(pid_str)))
        
    first_f = list(fechas_por_partida.values())[0] if fechas_por_partida else {}
    c.execute("""
        UPDATE sub_solicitudes_at
        SET estado = 'PROGRAMA_PROPUESTO', motivo_reprogramacion = NULL,
            fecha_recepcion_prog = ?, fecha_inicio_prog = ?,
            fecha_entrega_prog = ?, fecha_limite_prog = ?
        WHERE id = ?
    """, (first_f.get('recepcion'), first_f.get('inicio'), first_f.get('entrega'), first_f.get('limite'), sub_id))
    c.execute("UPDATE solicitudes_master SET estado = 'PROGRAMA_PROPUESTO' WHERE id = ?", (master_id,))
    conn.commit()
    conn.close()
    return {"status": "success", "message": "Fechas programadas enviadas a SSI con éxito."}

@app.get("/api/at/calendario-confirmado/{clave_area}")
def get_at_calendario_confirmado(clave_area: str):
    """Pestaña 3 CS-AT: Calendario de reservas y calibraciones confirmadas."""
    conn = db.get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT s.id as sub_id, m.no_folio, m.no_solicitud, m.no_cotizacion, m.cliente,
               m.representante as contacto,
               s.fecha_recepcion_prog, s.fecha_inicio_prog, s.fecha_entrega_prog
        FROM sub_solicitudes_at s
        JOIN solicitudes_master m ON s.solicitud_id = m.id
        WHERE s.clave_area = ? AND s.estado = 'PROGRAMA_CONFIRMADO'
        ORDER BY s.fecha_inicio_prog ASC
    """, (clave_area,))
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows

# ========================================================
# ENDPOINTS DE GENERACIÓN Y DESCARGA DE PDFS OFICIALES
# ========================================================

@app.get("/api/pdf/cotizacion/{solicitud_id}")
def download_cotizacion_pdf(solicitud_id: int):
    conn = db.get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM solicitudes_master WHERE id = ?", (solicitud_id,))
    sol = c.fetchone()
    if not sol:
        conn.close()
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")
    sol_dict = dict(sol)
    
    c.execute("""
        SELECT p.*, a.nombre as nombre_area
        FROM partidas p
        LEFT JOIN sub_solicitudes_at sub ON p.sub_solicitud_id = sub.id
        LEFT JOIN areas_tecnicas a ON sub.clave_area = a.clave
        WHERE p.solicitud_id = ?
        ORDER BY p.numero_partida
    """, (solicitud_id,))
    parts = [dict(p) for p in c.fetchall()]
    conn.close()
    
    os.makedirs("generated_docs", exist_ok=True)
    pdf_path = f"generated_docs/Cotizacion_{sol_dict['no_folio'].replace('-', '_')}_{sol_dict['no_cotizacion'] or 'DRAFT'}.pdf"
    pdf_gen.generate_cotizacion_pdf(sol_dict, parts, pdf_path)
    
    return FileResponse(
        path=pdf_path,
        media_type="application/pdf",
        filename=f"Cotizacion_{sol_dict['no_folio']}.pdf"
    )

@app.get("/api/pdf/programacion/{sub_id}")
def download_programacion_pdf(sub_id: int):
    conn = db.get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT sub.*, m.no_folio, m.no_solicitud, m.no_cotizacion, m.cliente, m.representante,
               m.telefono, m.correo, m.rfc, m.es_in_situ, m.orden_compra_cliente,
               m.fecha_aceptacion_cotizacion, a.nombre as nombre_area
        FROM sub_solicitudes_at sub
        JOIN solicitudes_master m ON sub.solicitud_id = m.id
        LEFT JOIN areas_tecnicas a ON sub.clave_area = a.clave
        WHERE sub.id = ?
    """, (sub_id,))
    sub_row = c.fetchone()
    if not sub_row:
        conn.close()
        raise HTTPException(status_code=404, detail="Sub-solicitud no encontrada")
    sub_dict = dict(sub_row)
    
    c.execute("SELECT * FROM partidas WHERE sub_solicitud_id = ? AND aceptada_cliente = 1 ORDER BY numero_partida", (sub_id,))
    parts = [dict(p) for p in c.fetchall()]
    conn.close()
    
    os.makedirs("generated_docs", exist_ok=True)
    pdf_path = f"generated_docs/Programacion_{sub_dict['no_folio'].replace('-', '_')}_{sub_dict['clave_area']}.pdf"
    sol_dict = {
        'no_folio': sub_dict['no_folio'],
        'no_solicitud': sub_dict['no_solicitud'],
        'no_cotizacion': sub_dict['no_cotizacion'],
        'cliente': sub_dict['cliente'],
        'representante': sub_dict['representante'],
        'telefono': sub_dict['telefono'],
        'correo': sub_dict['correo'],
        'rfc': sub_dict['rfc'],
        'orden_compra_cliente': sub_dict['orden_compra_cliente'],
        'fecha_aceptacion_cotizacion': sub_dict['fecha_aceptacion_cotizacion']
    }
    tipo_p = 'IN_SITU' if sub_dict.get('es_in_situ') else 'CENAM'
    pdf_gen.generate_programacion_pdf(sol_dict, sub_dict, parts, tipo=tipo_p, filepath=pdf_path)
    
    return FileResponse(
        path=pdf_path,
        media_type="application/pdf",
        filename=f"Programacion_{sub_dict['no_folio']}_{sub_dict['clave_area']}.pdf"
    )

@app.get("/api/pdf/contrato/{sub_id}")
def download_contrato_pdf(sub_id: int):
    conn = db.get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT sub.*, m.no_folio, m.no_solicitud, m.no_cotizacion, m.cliente, m.representante,
               m.telefono, m.correo, m.rfc, m.es_in_situ, m.orden_compra_cliente,
               m.fecha_aceptacion_cotizacion, m.modalidad_retorno, m.representante_legal_cenam,
               m.direccion_servicio_sitio, m.condiciones_acceso_planta,
               a.nombre as nombre_area
        FROM sub_solicitudes_at sub
        JOIN solicitudes_master m ON sub.solicitud_id = m.id
        LEFT JOIN areas_tecnicas a ON sub.clave_area = a.clave
        WHERE sub.id = ?
    """, (sub_id,))
    sub_row = c.fetchone()
    if not sub_row:
        conn.close()
        raise HTTPException(status_code=404, detail="Sub-solicitud no encontrada")
    sub_dict = dict(sub_row)
    
    c.execute("SELECT * FROM partidas WHERE sub_solicitud_id = ? AND aceptada_cliente = 1 ORDER BY numero_partida", (sub_id,))
    parts = [dict(p) for p in c.fetchall()]
    conn.close()
    
    os.makedirs("generated_docs", exist_ok=True)
    pdf_path = f"generated_docs/Contrato_{sub_dict['no_folio'].replace('-', '_')}_{sub_dict['clave_area']}.pdf"
    sol_dict = {
        'no_folio': sub_dict['no_folio'],
        'no_solicitud': sub_dict['no_solicitud'],
        'no_cotizacion': sub_dict['no_cotizacion'],
        'cliente': sub_dict['cliente'],
        'representante': sub_dict['representante'],
        'telefono': sub_dict['telefono'],
        'correo': sub_dict['correo'],
        'rfc': sub_dict['rfc'],
        'modalidad_retorno': sub_dict['modalidad_retorno'],
        'direccion_servicio_sitio': sub_dict['direccion_servicio_sitio'],
        'condiciones_acceso_planta': sub_dict['condiciones_acceso_planta'],
        'orden_compra_cliente': sub_dict['orden_compra_cliente']
    }
    tipo_p = 'IN_SITU' if sub_dict.get('es_in_situ') else 'CENAM'
    pdf_gen.generate_programacion_pdf(sol_dict, sub_dict, parts, tipo=tipo_p, filepath=pdf_path, rep_legal_cenam=sub_dict.get('representante_legal_cenam'))
    
    return FileResponse(
        path=pdf_path,
        media_type="application/pdf",
        filename=f"Contrato_Programacion_{sub_dict['no_folio']}_{sub_dict['clave_area']}.pdf"
    )

# ========================================================
# ENDPOINT DE MANTENIMIENTO (LIMPIEZA OPERATIVA)
# ========================================================

@app.post("/api/mantenimiento/limpiar-bd")
def limpiar_bd_operativa():
    res = db.limpiar_solicitudes_y_programaciones()
    return {"status": "success", "message": "Limpieza operativa completada con éxito. Catálogos protegidos.", "detalles": res}

# ========================================================
# INTERFAZ WEB COMPLETA DE USUARIO (DASHBOARD RESPONSIVO)
# ========================================================

@app.get("/", response_class=HTMLResponse)
@app.get("/ssi", response_class=HTMLResponse)
def index_page():
    return HTMLResponse(content=INDEX_HTML)

from ui_template import INDEX_HTML

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print(f"========================================================")
    print(f" Iniciando Servidor ASGI Uvicorn CENAM (1:1 Completo)")
    print(f" URL Web: http://127.0.0.1:{port}")
    print(f" Swagger API Docs: http://127.0.0.1:{port}/docs")
    print(f"========================================================")
    uvicorn.run("server:app", host="0.0.0.0", port=port, reload=True)
