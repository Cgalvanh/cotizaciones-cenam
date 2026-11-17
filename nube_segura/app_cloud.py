import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta, date
import cloud_db as cdb
import pdf_generator as pdf_gen
import request_parser as parser

st.set_page_config(
    page_title="CENAM - Nube Segura (Cotizaciones y Programación)",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inicializar Base de Datos Segura una sola vez en memoria (Optimización de Rendimiento)
@st.cache_resource(show_spinner=False)
def ensure_cloud_db_ready():
    cdb.init_cloud_db()
    return True

ensure_cloud_db_ready()

# Cache para estatus de conexión a BD (evita handshake de red en cada interacción)
@st.cache_resource(ttl=300, show_spinner=False)
def get_db_status():
    conn, engine = cdb.get_db_connection()
    ctype = getattr(conn, "connection_type", "SQLITE")
    conn.close()
    return engine, ctype

engine_probe, conn_type_probe = get_db_status()
current_db_url = cdb.get_database_url()

# Carga de alta velocidad y bajo consumo para datos estáticos (Catálogos y Áreas)
# Cachea en RAM por 1 hora para NO agotar las cuotas de Supabase ni saturar conexiones
@st.cache_data(ttl=3600, show_spinner=False)
def load_cached_catalog_data():
    conn, engine = cdb.get_db_connection()
    c = conn.cursor()
    # 1. Áreas Técnicas
    c.execute("SELECT clave, nombre, id_area, direccion FROM areas_tecnicas ORDER BY clave")
    areas_list = [dict(r) for r in c.fetchall()]
    areas_map = {a['clave']: a['nombre'] for a in areas_list}
    areas_dir_map = {a['clave']: a.get('direccion', '') for a in areas_list}
    
    # 2. Catálogo de Servicios
    c.execute("""
        SELECT clave_servicio, supuesto, alcance, observaciones, costo, dias_habiles_defecto, es_in_situ,
               codigo_laboratorio, nombre_laboratorio, clave_area, codigo_division, metodo, incertidumbre
        FROM catalogo_servicios
        ORDER BY clave_area, codigo_laboratorio, clave_servicio
    """)
    servs_list = [dict(r) for r in c.fetchall()]
    serv_by_clave = {s['clave_servicio']: s for s in servs_list}
    
    from collections import defaultdict
    serv_by_area = defaultdict(list)
    for s in servs_list:
        if s.get('clave_area'):
            serv_by_area[str(s['clave_area'])].append(s)
            
    # 3. Laboratorios
    c.execute("""
        SELECT DISTINCT codigo, descripcion, id_division, id_area, clave_area
        FROM laboratorios
        WHERE es_laboratorio = 1 AND activo = 1
        ORDER BY clave_area, codigo
    """)
    labs_list = [dict(r) for r in c.fetchall()]
    labs_by_area = defaultdict(list)
    for lab in labs_list:
        if lab.get('clave_area'):
            labs_by_area[str(lab['clave_area'])].append(lab)
            
    conn.close()
    return areas_list, areas_map, areas_dir_map, serv_by_clave, serv_by_area, labs_by_area

areas_tecnicas, areas_dict, areas_dir_dict, serv_by_clave, serv_by_area, labs_by_area = load_cached_catalog_data()

# Helpers
def get_sla_badge(fecha_asig_str):
    try:
        f_asig = datetime.strptime(fecha_asig_str, "%Y-%m-%d %H:%M:%S")
        dias_transcurridos = (datetime.now() - f_asig).days
        if dias_transcurridos <= 1:
            return f"🟢 {dias_transcurridos} día(s) (En tiempo)"
        elif dias_transcurridos <= 3:
            return f"🟡 {dias_transcurridos} día(s) (Próximo a vencer - SLA 3 días)"
        else:
            return f"🔴 {dias_transcurridos} día(s) (VENCIDO - Excede 3 días)"
    except Exception:
        return "SLA 3 días hábiles"

# Banner de Mensajes Flash persistentes entre recargas (rerun)
if "flash_msg" in st.session_state:
    m_type, m_text = st.session_state["flash_msg"]
    if m_type == "success":
        st.success(m_text, icon="✅")
    elif m_type == "warning":
        st.warning(m_text, icon="⚠️")
    elif m_type == "info":
        st.info(m_text, icon="ℹ️")
    del st.session_state["flash_msg"]

# Session State para Autenticación Segura (RBAC)
if "user" not in st.session_state:
    st.session_state["user"] = None

# ==========================================
# PANTALLA 0: INICIO DE SESIÓN SEGURO (ZERO TRUST)
# ==========================================
if st.session_state["user"] is None:
    col_top1, col_top2, col_top3 = st.columns([1, 1.2, 1])
    with col_top2:
        logo_img = "nube_segura/static/logo_cenam.png" if os.path.exists("nube_segura/static/logo_cenam.png") else "static/img/logo_cenam.png"
        if os.path.exists(logo_img):
            st.image(logo_img, width=260)
            
    st.markdown("<h2 style='text-align: center; color: #1A365D; margin-top: -10px;'>Centro Nacional de Metrología</h2>", unsafe_allow_html=True)
    st.markdown("<h4 style='text-align: center; color: #8C6D23;'>Plataforma Institucional de Cotización, Programación y DSNR PR</h4>", unsafe_allow_html=True)
    st.write("")
    
    col_l1, col_l2, col_l3 = st.columns([1, 1.3, 1])
    with col_l2:
        if engine_probe == "POSTGRES":
            st.success(f"☁️ **Conectado a Base de Datos PostgreSQL Supabase** (`{conn_type_probe}`)", icon="✅")
        else:
            if "[YOUR-PASSWORD]" in current_db_url or not current_db_url:
                with st.expander("⚙️ Conexión Supabase PostgreSQL (Requiere Contraseña)", expanded=True):
                    st.info("URI configurada: `postgresql://postgres.lmvpzqniqjhdtjmmxvdg:[PASSWORD]@aws-0-us-east-1.pooler.supabase.com:5432/postgres` (Connection Pooler IPv4 Oficial)")
                    st.caption("Ingrese la contraseña que asignó a su base de datos Supabase para conectar:")
                    supa_pwd = st.text_input("Contraseña de Supabase:", type="password", key="supa_pwd_box")
                    if st.button("🔌 Probar y Conectar a Supabase", type="primary"):
                        if not supa_pwd:
                            st.warning("Ingrese su contraseña de Supabase.")
                        else:
                            test_url = f"postgresql://postgres.lmvpzqniqjhdtjmmxvdg:{supa_pwd.strip()}@aws-0-us-east-1.pooler.supabase.com:5432/postgres?sslmode=prefer"
                            with st.spinner("Probando conexión a Supabase..."):
                                ok, msg, m_type = cdb.test_postgres_connection(test_url)
                            if ok:
                                cdb.update_supabase_password(supa_pwd.strip())
                                cdb.init_cloud_db()
                                st.session_state["flash_msg"] = ("success", f"🎉 Conexión exitosa a Supabase ({m_type}). Base de datos sincronizada.")
                                st.rerun()
                            else:
                                st.error(f"No se pudo conectar a Supabase: {msg}")
            else:
                st.warning("⚠️ Operando con SQLite local de respaldo (PostgreSQL no disponible).", icon="⚠️")

        with st.container(border=True):
            st.subheader("Acceso Autenticado Institucional")
            st.caption("Conexión cifrada TLS 1.3 con almacenamiento seguro AES-256.")
            
            correo_input = st.text_input("Correo Institucional (@cenam.mx)", placeholder="usuario@cenam.mx")
            pwd_input = st.text_input("Contraseña", type="password")
            
            st.write("")
            btn_login = st.button("🔐 Iniciar Sesión Segura", type="primary", width="stretch")
            
            if btn_login:
                usuario = cdb.verify_credentials(correo_input.strip().lower(), pwd_input)
                if usuario:
                    st.session_state["user"] = usuario
                    cdb.log_auditoria(usuario['correo'], "LOGIN_EXITOSO", "USUARIO", usuario['id'], {"ip": "CloudRun_Client"})
                    st.session_state["flash_msg"] = ("success", f"Bienvenido(a), {usuario['nombre_completo']} ({usuario['rol']})")
                    st.rerun()
                else:
                    st.error("Credenciales incorrectas o cuenta inactiva. Verifique correo y contraseña.")
                    cdb.log_auditoria(correo_input, "LOGIN_FALLIDO", "USUARIO", None, {"intento": "Password erróneo"})

            st.markdown("---")
            st.markdown("**Credenciales de demostración precargadas:**")
            st.caption("• **Ventanilla SSI:** `ssi@cenam.mx` | Contraseña: `Cenam2026*`")
            st.caption("• **División Metrología Dimensional (740):** `at.dimensional@cenam.mx` | Contraseña: `Cenam2026*`")
            st.caption("• **División Metrología Eléctrica (410):** `at.electrica@cenam.mx` | Contraseña: `Cenam2026*`")
            st.caption("• **División Fuerza y Presión (720):** `at.presion@cenam.mx` | Contraseña: `Cenam2026*`")
            st.caption("• **División Masa y Densidad (730):** `at.masa@cenam.mx` | Contraseña: `Cenam2026*`")
            st.caption("• **Administrador:** `admin@cenam.mx` | Contraseña: `Cenam2026*`")
    st.stop()

# ==========================================
# SESIÓN AUTENTICADA: ROLES Y PERMISOS
# ==========================================
user = st.session_state["user"]
rol = user['rol']
clave_area = user['clave_area']

# Sidebar con datos de sesión
logo_side = "nube_segura/static/logo_cenam.png" if os.path.exists("nube_segura/static/logo_cenam.png") else "static/img/logo_cenam.png"
if os.path.exists(logo_side):
    st.sidebar.image(logo_side, width=190)

st.sidebar.markdown(f"**Usuario:** {user['nombre_completo']}")
st.sidebar.markdown(f"**Rol Institucional:** `{rol}`")
if clave_area:
    st.sidebar.markdown(f"**División Asignada:** `{clave_area}` - {areas_dict.get(clave_area, '')}")
    if areas_dir_dict.get(clave_area):
        st.sidebar.caption(f"🏛️ {areas_dir_dict.get(clave_area)}")
st.sidebar.caption("🔒 Sesión Cifrada Activa (TLS 1.3 / AES-256)")
if engine_probe == "POSTGRES":
    st.sidebar.success(f"☁️ Supabase PostgreSQL ({conn_type_probe})", icon="✅")
else:
    st.sidebar.info("💾 Base Local (SQLite Respaldo)", icon="💾")

if rol == "ADMIN":
    vista_admin = st.sidebar.radio("Modo de Visualización (Admin):", ["🏢 Ventanilla Central (SSI)", "🔬 Área Técnica (AT)"])
else:
    vista_admin = None

if st.sidebar.button("🚪 Cerrar Sesión Segura"):
    cdb.log_auditoria(user['correo'], "LOGOUT", "USUARIO", user['id'], {})
    st.session_state["user"] = None
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.caption("Servidor en Google Cloud Run conectado a Base de Datos Centralizada")

# Determinar vista SSI o AT
mostrar_ssi = (rol == "SSI") or (rol == "ADMIN" and vista_admin == "🏢 Ventanilla Central (SSI)")

# ==========================================
# VISTA 1: ROL SSI (VENTANILLA CENTRAL - CS)
# ==========================================
if mostrar_ssi:
    st.title("🏢 Ventanilla Central (SSI) - Nube Segura")
    st.markdown("Gestión integral de solicitudes, cotizaciones consolidadas, programación de fechas por AT y formalización de contratos.")
    
    conn, engine = cdb.get_db_connection()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM sub_solicitudes_at WHERE estado = 'DEVUELTA'")
    devueltas_count = c.fetchone()[0] or 0
    
    c.execute("""
        SELECT COUNT(DISTINCT m.id)
        FROM solicitudes_master m
        JOIN sub_solicitudes_at s ON m.id = s.solicitud_id
        WHERE m.estado IN ('TURNADA', 'EMITIDA')
        GROUP BY m.id
        HAVING COUNT(s.id) = SUM(CASE WHEN s.estado = 'COMPLETADA' THEN 1 ELSE 0 END)
    """)
    cotiz_listas = len(c.fetchall())
    
    c.execute("SELECT COUNT(*) FROM solicitudes_master WHERE estado = 'COTIZACION_ENVIADA'")
    esperando_acep = c.fetchone()[0] or 0
    
    c.execute("SELECT COUNT(DISTINCT s.id) FROM sub_solicitudes_at s WHERE s.estado = 'PROGRAMA_PROPUESTO'")
    prog_propuestas = c.fetchone()[0] or 0
    conn.close()
    
    if devueltas_count > 0:
        st.warning(f"⚠️ **Atención SSI:** Hay **{devueltas_count} solicitud(es) devuelta(s)** por Áreas Técnicas que requieren reasignación.", icon="⚠️")
    if cotiz_listas > 0:
        st.info(f"🔔 **Aviso SSI:** Hay **{cotiz_listas} cotización(es)** listas para consolidar y emitir.", icon="🔔")
    if prog_propuestas > 0:
        st.info(f"📅 **Aviso Programación:** Hay **{prog_propuestas} programa(s) de fechas** propuestos por Laboratorios listos para enviar al cliente.", icon="📅")

    t1, t2, t3, t4, t5, t6 = st.tabs([
        "📝 1. Nueva Solicitud",
        f"⚠️ 2. Devueltas ({devueltas_count})",
        f"🏷️ 3. Emisión Cotización ({cotiz_listas})",
        f"📅 4. Aceptación y Programación ({esperando_acep + prog_propuestas})",
        "📜 5. Contratos y Confirmación",
        "🔍 6. Bitácora Auditoría"
    ])
    
    # TAB 1: NUEVA SOLICITUD
    with t1:
        st.subheader("Captura de Solicitud de Calibración (Formato Solicitud CENAM PR)")
        with st.expander("📥 Carga Rápida desde Formato Oficial o Correo (Cero Transcripción)", expanded=True):
            st.caption("Obtenga automáticamente todos los datos del cliente y sus instrumentos sin transcribir a mano. Puede subir el archivo `.docx` o `.txt` enviado por el cliente o pegar el cuerpo del correo.")
            col_u1, col_u2 = st.columns([1, 1])
            with col_u1:
                up_doc_c = st.file_uploader("Opción A: Subir archivo Solicitud CENAM PR (.docx o .txt):", type=["docx", "txt"], key="up_sol_doc_cloud")
            with col_u2:
                raw_email_text = st.text_area("Opción B: O pegar texto / cuerpo de correo recibido:", height=95, placeholder="SOLICITUD DE COTIZACIÓN DE SERVICIO DE CALIBRACIÓN...\n1. Datos del solicitante...\n2. Información del instrumento...", key="raw_email_input_cloud")
            
            if st.button("✨ Auto-extraer Datos y Llenar Formulario", key="btn_parse_cloud", type="primary", width="stretch"):
                parsed = None
                if up_doc_c is not None:
                    parsed = parser.parse_solicitud_input(file_source=up_doc_c)
                elif raw_email_text and raw_email_text.strip():
                    parsed = parser.parse_solicitud_input(raw_text=raw_email_text)
                    
                if parsed and (parsed.get("empresa") or parsed.get("instrumentos") or parsed.get("no_solicitud")):
                    st.session_state["parsed_cloud"] = parsed
                    st.session_state["form_v_cloud"] = st.session_state.get("form_v_cloud", 0) + 1
                    inst_count = len(parsed.get("instrumentos", []))
                    st.session_state["flash_msg"] = ("success", f"✨ Datos extraídos exitosamente: Cliente: **{parsed['empresa'] or 'Detectado'}** | **{inst_count} instrumento(s)** clasificados por Área Técnica.")
                    st.rerun()
                else:
                    st.warning("⚠️ No se detectaron datos suficientes en el archivo o texto proporcionado. Verifique que corresponda al formato oficial de Solicitud CENAM PR.")

        parsed_data = st.session_state.get("parsed_cloud", {})
        form_v_cloud = st.session_state.get("form_v_cloud", 0)
        
        with st.form("form_nueva_sol_cloud", clear_on_submit=True):
            st.markdown("#### 1. Datos del Solicitante")
            c1, c2, c3 = st.columns(3)
            with c1:
                cliente = st.text_input("Razón Social / Nombre del Cliente *", value=parsed_data.get("empresa") or "ECOLOGIA INTEGRADA APLICADA", key=f"c_cli_{form_v_cloud}")
                representante = st.text_input("Representante / Contacto", value=parsed_data.get("contacto") or "Ing. Alba Vázquez Espinosa", key=f"c_rep_{form_v_cloud}")
            with c2:
                correo = st.text_input("Correo Electrónico *", value=parsed_data.get("correo") or "alba_ecol@hotmail.com", key=f"c_mail_{form_v_cloud}")
                telefono = st.text_input("Teléfono", value=parsed_data.get("telefono") or "961 61 591 19", key=f"c_tel_{form_v_cloud}")
            with c3:
                rfc = st.text_input("RFC", value=parsed_data.get("rfc") or "EIA050512XYZ", key=f"c_rfc_{form_v_cloud}")
                pais = st.text_input("País de Solicitud *", value=parsed_data.get("pais") or "México", key=f"c_pais_{form_v_cloud}")
                
            st.markdown("---")
            st.markdown("#### 2. Consecutivos Institucionales y Modalidad del Expediente")
            c_fol1, c_fol2 = st.columns([1.5, 2])
            with c_fol1:
                next_fol = parsed_data.get("no_folio") or cdb.get_next_folio_number()
                st.info(f"📁 **No. de Folio Asignado:** `{next_fol}`")
            with c_fol2:
                st.caption("ℹ️ **Regla Operativa CENAM (1 Folio ➔ N Solicitudes):** SSI asigna este único Folio maestro para la trazabilidad integral del expediente cliente. El sistema generará una Solicitud independiente con consecutivo PR para cada Área Técnica / División y para los servicios que se realicen IN SITU con viáticos.")
                
            es_extranjero = (pais.strip().lower() != "mexico" and pais.strip().lower() != "méxico")
            if es_extranjero:
                st.warning(f"⚠️ Solicitante en el extranjero detectado ({pais}). En términos de la Ley del IVA, el impuesto no aplica si el servicio es aprovechado en su totalidad en el extranjero.")
                aplica_iva = st.checkbox("¿Exentar IVA (0%) para este cliente extranjero?", value=True, key=f"c_iva_{form_v_cloud}")
            else:
                aplica_iva = st.checkbox("Aplica IVA general del 16%", value=True, key=f"c_iva_{form_v_cloud}")
                
            st.markdown("---")
            st.markdown("#### 3. Instrumentos a Calibrar y Clasificación por División / Modalidad")
            parsed_inst = parsed_data.get("instrumentos", [])
            num_default = len(parsed_inst) if parsed_inst else 2
            num_eq = st.number_input("Cantidad de Instrumentos:", min_value=1, max_value=30, value=num_default, key=f"c_numeq_{form_v_cloud}")
            
            eq_list = []
            for i in range(int(num_eq)):
                p_item = parsed_inst[i] if i < len(parsed_inst) else {}
                st.markdown(f"**Instrumento {i+1}**")
                ce1, ce2, ce3, ce4 = st.columns([3, 2, 2, 1.2])
                with ce1:
                    d_eq = st.text_input(f"Descripción Instrumento {i+1} *", value=p_item.get("descripcion") or ("Detector de fugas acústico" if i==0 else "Multímetro digital 6.5 dígitos"), key=f"c_desc_{i}_{form_v_cloud}")
                    alc_eq = st.text_input(f"Alcance / Puntos requeridos {i+1}", value=p_item.get("intervalo") or ("<= 80 kHz" if i==0 else "100 mV a 1000 V"), key=f"c_alc_{i}_{form_v_cloud}")
                    cert_eq = st.text_input(f"Certificado anterior o No. equipo CENAM {i+1}", value=p_item.get("certificado_anterior") or "", key=f"c_cert_{i}_{form_v_cloud}")
                with ce2:
                    m_eq = st.text_input(f"Marca {i+1}", value=p_item.get("marca") or ("Mesa Engineering" if i==0 else "Fluke"), key=f"c_m_{i}_{form_v_cloud}")
                    mod_eq = st.text_input(f"Modelo {i+1}", value=p_item.get("modelo") or ("2D" if i==0 else "8846A"), key=f"c_mod_{i}_{form_v_cloud}")
                    mag_eq = st.text_input(f"Magnitud {i+1}", value=p_item.get("magnitud") or ("Vibraciones y Acústica" if i==0 else "Eléctrica"), key=f"c_mag_{i}_{form_v_cloud}")
                with ce3:
                    s_eq = st.text_input(f"No. Serie {i+1}", value=p_item.get("serie") or f"SN-{2000+i}", key=f"c_s_{i}_{form_v_cloud}")
                    id_eq = st.text_input(f"Identificación Interna {i+1}", value=p_item.get("id_interno") or f"PR-EQ-{i+1:02d}", key=f"c_id_{i}_{form_v_cloud}")
                    sug_at = p_item.get("clave_area_sugerida") or parser.sugerir_area_por_magnitud_y_texto(mag_eq, d_eq)
                    # Equivalencias si sug_at es clave antigua
                    mapping_old_at = {'AT-01': '740', 'AT-02': '410', 'AT-03': '440', 'AT-04': '430', 'AT-05': '420', 'AT-06': '520', 'AT-07': '730', 'AT-08': '720', 'AT-09': '710', 'AT-10': '510', 'AT-11': '700', 'AT-12': '630', 'AT-13': '620', 'AT-14': '810'}
                    sug_at = mapping_old_at.get(sug_at, sug_at)
                    at_dest = st.selectbox(
                        f"División Destino {i+1}",
                        options=list(areas_dict.keys()),
                        format_func=lambda x: f"{x} - {areas_dict[x]} [{areas_dir_dict.get(x, '')}]" if areas_dir_dict.get(x) else f"{x} - {areas_dict[x]}",
                        index=list(areas_dict.keys()).index(sug_at) if sug_at in areas_dict else 0,
                        key=f"c_at_{i}_{form_v_cloud}"
                    )
                with ce4:
                    it_insitu = st.checkbox(f"🚗 IN SITU {i+1}", value=False, key=f"c_insitu_{i}_{form_v_cloud}", help="Marque si este servicio se realizará en planta del cliente con viáticos.")
                cond_eq = st.text_input(f"Condiciones particulares de calibración {i+1} (Opcional)", value=p_item.get("condiciones") or "", key=f"c_cond_{i}_{form_v_cloud}")
                eq_list.append({"num": i+1, "desc": d_eq, "marca": m_eq, "modelo": mod_eq, "serie": s_eq, "alcance": alc_eq, "cert": cert_eq, "mag": mag_eq, "id": id_eq, "cond": cond_eq, "area": at_dest, "clave_area": at_dest, "es_in_situ": 1 if it_insitu else 0})
                st.divider()
                
            # Previsualización del Desagregado
            from collections import defaultdict
            pre_grupos = defaultdict(int)
            for it in eq_list:
                mod_name = "🚗 IN SITU (Viáticos)" if it['es_in_situ'] else "🔬 LAB CENAM"
                pre_grupos[(it['clave_area'], mod_name)] += 1
                
            st.markdown("##### 🔍 Previsualización de Solicitudes a Generar:")
            c_prev_cols = st.columns(len(pre_grupos) or 1)
            for idx_g, ((g_area, g_mod), g_count) in enumerate(pre_grupos.items()):
                with c_prev_cols[idx_g % len(c_prev_cols)]:
                    st.success(f"**División {g_area}**\n\n{areas_dict.get(g_area, '')}\n\n`{g_mod}`: **{g_count} partida(s)**")
                    
            btn_guardar_cloud = st.form_submit_button("🚀 Registrar Expediente y Generar Solicitudes en Nube", type="primary")
            
            if btn_guardar_cloud:
                cliente_dict = {
                    "cliente": cliente,
                    "representante": representante,
                    "telefono": telefono,
                    "correo": correo,
                    "rfc": rfc,
                    "pais": pais,
                    "es_extranjero": es_extranjero,
                    "aplica_iva": aplica_iva
                }
                
                res = cdb.crear_expediente_y_solicitudes(cliente_dict, eq_list, user['correo'])
                
                if "parsed_cloud" in st.session_state:
                    del st.session_state["parsed_cloud"]
                    
                detalles_sol = []
                for sc in res["solicitudes_creadas"]:
                    mod_tag = "🚗 IN SITU (Viáticos)" if sc["es_in_situ"] else "🔬 LAB CENAM"
                    detalles_sol.append(f"• **Solicitud {sc['no_solicitud']}**: {sc['clave_area']} - {areas_dict.get(sc['clave_area'], '')} [{mod_tag}] con {sc['total_partidas']} partida(s)")
                    
                st.session_state["flash_msg"] = (
                    "success",
                    f"🚀 **Expediente Registrado con Folio Maestro {res['no_folio']}**\n\n" +
                    "Se generaron las siguientes solicitudes independientes turnadas a las Áreas Técnicas correspondientes:\n\n" +
                    "\n".join(detalles_sol)
                )
                st.toast(f"Expediente {res['no_folio']} registrado con éxito", icon="📤")
                st.rerun()

    # TAB 2: SOLICITUDES DEVUELTAS
    with t2:
        st.subheader("Bandeja de Solicitudes Devueltas por Áreas Técnicas (No Corresponde)")
        conn, engine = cdb.get_db_connection()
        c = conn.cursor()
        c.execute("""
            SELECT s.id as sub_id, m.id as master_id, m.no_folio, m.no_solicitud, m.cliente,
                   s.clave_area as area_actual, s.motivo_devolucion, s.area_sugerida, s.fecha_asignacion
            FROM sub_solicitudes_at s
            JOIN solicitudes_master m ON s.solicitud_id = m.id
            WHERE s.estado = 'DEVUELTA'
            ORDER BY s.id DESC
        """)
        devueltas = c.fetchall()
        conn.close()
        
        if not devueltas:
            st.info("No hay solicitudes devueltas pendientes de reasignación. ¡Todo el flujo está en orden!")
        else:
            for d in devueltas:
                with st.expander(f"🔴 Folio: {d['no_folio']} | Solicitud: {d['no_solicitud']} | Cliente: {d['cliente']}", expanded=True):
                    col_d1, col_d2 = st.columns([3, 2])
                    with col_d1:
                        st.markdown(f"**Área que la devolvió:** {d['area_actual']} - {areas_dict.get(d['area_actual'], '')}")
                        st.error(f"**Motivo de Devolución indicado por el AT:**\n{d['motivo_devolucion']}")
                        if d['area_sugerida']:
                            st.info(f"💡 **Área sugerida por el AT:** {d['area_sugerida']} - {areas_dict.get(d['area_sugerida'], '')}")
                    with col_d2:
                        sug_idx = list(areas_dict.keys()).index(d['area_sugerida']) if d['area_sugerida'] in areas_dict else 0
                        nueva_at = st.selectbox(
                            "Reasignar a nueva Área Técnica:",
                            options=list(areas_dict.keys()),
                            format_func=lambda x: f"{x} - {areas_dict[x]} [{areas_dir_dict.get(x, '')}]" if areas_dir_dict.get(x) else f"{x} - {areas_dict[x]}",
                            index=sug_idx,
                            key=f"reasig_cloud_{d['sub_id']}"
                        )
                        if st.button("🔄 Confirmar Reasignación en Nube", key=f"btn_r_c_{d['sub_id']}"):
                            conn, engine = cdb.get_db_connection()
                            c = conn.cursor()
                            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            c.execute("""
                            UPDATE sub_solicitudes_at
                            SET clave_area = ?, estado = 'ASIGNADA', motivo_devolucion = NULL,
                                area_sugerida = NULL, fecha_asignacion = ?, fecha_limite_sla = ?
                            WHERE id = ?
                            """, (nueva_at, now_str, (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d"), d['sub_id']))
                            conn.commit()
                            conn.close()
                            
                            cdb.log_auditoria(user['correo'], "REASIGNAR_SOLICITUD", "SUB_SOLICITUD", d['sub_id'], {"folio": d['no_folio'], "nueva_area": nueva_at})
                            st.session_state["flash_msg"] = (
                                "success",
                                f"🔄 Solicitud **{d['no_folio']}** reasignada exitosamente a **{nueva_at} - {areas_dict.get(nueva_at, '')}**. Desaparece de esta bandeja y el nuevo AT ha sido notificado."
                            )
                            st.toast(f"Folio {d['no_folio']} reasignado a {nueva_at}", icon="🔄")
                            st.rerun()

    # TAB 3: EMISIÓN DE COTIZACIÓN
    with t3:
        st.subheader("Consolidación y Emisión de Cotización Oficial / DSNR hacia el Cliente")
        modo_vista_t3 = st.radio("Modo de Consulta:", ["📋 Consolidación por Solicitud", "📁 Vista Integral de Expedientes (1 Folio ➔ N Solicitudes)"], horizontal=True, key="modo_t3_cloud")
        
        if modo_vista_t3 == "📁 Vista Integral de Expedientes (1 Folio ➔ N Solicitudes)":
            expedientes_all = cdb.get_expedientes_resumen()
            if not expedientes_all:
                st.info("No hay expedientes registrados en el sistema.")
            else:
                st.caption(f"Mostrando {len(expedientes_all)} expedientes agrupados por Folio maestro:")
                for exp in expedientes_all:
                    total_hijas = len(exp["solicitudes"])
                    with st.expander(f"📁 Folio: {exp['no_folio']} | Cliente: {exp['cliente']} | RFC: {exp['rfc'] or 'N/A'} ({total_hijas} solicitud(es) hija(s))", expanded=False):
                        st.markdown(f"**Fecha de Recepción:** `{exp['fecha_recepcion']}`")
                        
                        sol_table = []
                        for h in exp["solicitudes"]:
                            mod_txt = "🚗 IN SITU (Viáticos)" if h["es_in_situ"] else "🔬 LAB CENAM"
                            sol_table.append({
                                "No. Solicitud": h["no_solicitud"],
                                "División": f"{h['clave_area'] or ''} - {h['nombre_area'] or ''}",
                                "Modalidad": mod_txt,
                                "Partidas": h["total_partidas"],
                                "Estado": h["estado"],
                                "No. Cotización": h["no_cotizacion"] or "Pendiente"
                            })
                        st.dataframe(pd.DataFrame(sol_table), width="stretch")
        else:
            conn, engine = cdb.get_db_connection()
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
            solicitudes = c.fetchall()
            
            # OPTIMIZACIÓN SUPABASE: Consulta por lotes (Batch Query) de todas las partidas
            # Reduce de N consultas a 1 sola consulta masiva para evitar agotar el pooler de conexiones
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
        
        if not solicitudes:
            st.success("🎉 No hay cotizaciones pendientes de emitir. Todas han sido despachadas al cliente.")
        else:
            for s in solicitudes:
                is_ready = (s['total_subs'] > 0 and s['total_subs'] == s['subs_completadas'])
                tag = "✅ LISTA PARA CONSOLIDAR Y ENVIAR" if is_ready else f"⏳ EN PROCESO ({s['subs_completadas']}/{s['total_subs']} áreas terminadas)"
                with st.expander(f"Folio: {s['no_folio']} | Solicitud: {s['no_solicitud']} | {s['cliente']} [{tag}]", expanded=is_ready):
                    parts = partidas_por_sol.get(s['id'], [])
                    
                    # AUTO-REPARACIÓN PREVENTIVA: Si una partida viable tiene servicio de catálogo pero costo $0.00
                    hubo_auto_fix = False
                    conn_fix = None
                    for p in parts:
                        if p['es_no_realizable'] == 0:
                            p_u = float(p.get('precio_unitario') or 0.0)
                            c_serv = p.get('clave_servicio')
                            if (p_u <= 0.0 or not p.get('descripcion_servicio')) and c_serv and c_serv in serv_by_clave:
                                s_cat = serv_by_clave[c_serv]
                                nuevo_precio = float(s_cat.get('costo') or 0.0)
                                if nuevo_precio > 0.0:
                                    cant_val = int(p.get('cantidad') or 1)
                                    tot_val = nuevo_precio * cant_val
                                    p['precio_unitario'] = nuevo_precio
                                    p['precio_total'] = tot_val
                                    if not p.get('descripcion_servicio'):
                                        p['descripcion_servicio'] = s_cat.get('supuesto') or ""
                                    if not conn_fix:
                                        conn_fix, _ = cdb.get_db_connection()
                                    c_fix = conn_fix.cursor()
                                    c_fix.execute("""
                                        UPDATE partidas
                                        SET precio_unitario = ?, precio_total = ?, descripcion_servicio = ?
                                        WHERE id = ?
                                    """, (nuevo_precio, tot_val, p['descripcion_servicio'], p['id']))
                                    hubo_auto_fix = True
                    if conn_fix:
                        conn_fix.commit()
                        conn_fix.close()
                    
                    parts_display = []
                    subtot_viable = 0.0
                    comentarios_ssi_list = []
                    for p in parts:
                        cant_p = int(p.get('cantidad') or 1)
                        p_unit = float(p.get('precio_unitario') or 0.0)
                        p_tot = float(p.get('precio_total') or (p_unit * cant_p))
                        if p['es_no_realizable'] == 0:
                            subtot_viable += p_tot
                        if p.get('comentarios_ssi'):
                            comentarios_ssi_list.append((p['numero_partida'], p['nombre_area'] or '', p['comentarios_ssi']))
                        parts_display.append({
                            "Part.": p['numero_partida'],
                            "Área": p['nombre_area'],
                            "Equipo": p['descripcion_equipo'],
                            "Marca/Modelo": f"{p['marca'] or ''} {p['modelo'] or ''}",
                            "ID": p['id_interno'] or '',
                            "Servicio": p['descripcion_servicio'] or "Pendiente de cotizar",
                            "Cant.": cant_p,
                            "Costo Unitario": f"${p_unit:,.2f}",
                            "Costo Total": f"${p_tot:,.2f}",
                            "Días Hábiles": p['tiempo_dias_habiles'],
                            "Comentarios Cliente": p.get('comentarios_cliente') or "—",
                            "Estado": "🔴 DSNR" if p['es_no_realizable'] == 1 else "🟢 Realizable"
                        })
                    st.dataframe(pd.DataFrame(parts_display), width="stretch")
                    
                    if comentarios_ssi_list:
                        with st.expander("🔒 Ver Comentarios Internos de las Áreas Técnicas para SSI (No visibles al cliente)"):
                            for num_p, a_nom, c_ssi in comentarios_ssi_list:
                                st.info(f"**Partida {num_p} [{a_nom}]:** {c_ssi}")
                                
                    # Resumen financiero con IVA del 16%
                    iva_tot = subtot_viable * 0.16 if s['aplica_iva'] else 0.0
                    tot_gral = subtot_viable + iva_tot
                    c_f1, c_f2, c_f3 = st.columns(3)
                    with c_f1:
                        st.metric("Subtotal Cotización", f"${subtot_viable:,.2f}")
                    with c_f2:
                        st.metric("I.V.A. (16%)", f"${iva_tot:,.2f}" if s['aplica_iva'] else "$0.00 (Exento)")
                    with c_f3:
                        st.metric("Total Cotización", f"${tot_gral:,.2f}")
                    
                    has_viable = any(p['es_no_realizable'] == 0 for p in parts)
                    has_dsnr = any(p['es_no_realizable'] == 1 for p in parts)
                    
                    # FILTRO DE CALIDAD ESTRICTO: Detección de partidas en $0.00 o sin servicio
                    ceros_parts = [p for p in parts if p['es_no_realizable'] == 0 and (float(p.get('precio_unitario') or 0.0) <= 0.0 or not p.get('clave_servicio'))]
                    hay_ceros = len(ceros_parts) > 0
                    
                    if hay_ceros:
                        st.error(
                            f"⚠️ **Atención SSI: Existen {len(ceros_parts)} partida(s) con costo $0.00 o sin servicio asignado.**\n\n"
                            "Por normativa institucional, no es posible emitir la cotización oficial hasta que todas las partidas viables tengan precio."
                        )
                        c_fix_col1, c_fix_col2 = st.columns([3, 2])
                        with c_fix_col1:
                            with st.expander("🛠️ Corrección Rápida de Precios por SSI (Asignar del Catálogo)", expanded=True):
                                for cp in ceros_parts:
                                    st.markdown(f"**Partida {cp['numero_partida']}:** `{cp['descripcion_equipo']}` [{cp.get('nombre_area') or 'Área Técnica'}]")
                                    # Buscar servicios del área correspondiente o catálogo general
                                    area_c = str(s.get('clave_area') or '')
                                    servs_opts = serv_by_area.get(area_c, [])
                                    if not servs_opts:
                                        servs_opts = list(serv_by_clave.values())[:100]
                                    s_map_ssi = {
                                        srv['clave_servicio']: f"[{srv.get('codigo_laboratorio') or 'GRAL'}] {srv['clave_servicio']} - {srv['supuesto'][:60]}... (${float(srv['costo']):,.2f})"
                                        for srv in servs_opts
                                    }
                                    if s_map_ssi:
                                        s_fix_sel = st.selectbox(
                                            "Servicio sugerido:",
                                            options=list(s_map_ssi.keys()),
                                            format_func=lambda x: s_map_ssi[x],
                                            key=f"c_fix_ssel_{cp['id']}"
                                        )
                                        if st.button("💾 Guardar y Asignar Precio a esta Partida", key=f"c_btn_fix_{cp['id']}"):
                                            s_chosen = serv_by_clave[s_fix_sel]
                                            p_unit_fix = float(s_chosen['costo'])
                                            cant_fix = int(cp.get('cantidad') or 1)
                                            tot_fix = p_unit_fix * cant_fix
                                            conn, engine = cdb.get_db_connection()
                                            c = conn.cursor()
                                            c.execute("""
                                                UPDATE partidas
                                                SET clave_servicio = ?, descripcion_servicio = ?,
                                                    precio_unitario = ?, precio_total = ?,
                                                    tiempo_dias_habiles = ?
                                                WHERE id = ?
                                            """, (s_fix_sel, s_chosen['supuesto'], p_unit_fix, tot_fix, s_chosen.get('dias_habiles_defecto') or 5, cp['id']))
                                            conn.commit()
                                            conn.close()
                                            cdb.log_auditoria(user['correo'], "CORREGIR_PRECIO_PARTIDA", "PARTIDA", cp['id'], {"servicio": s_fix_sel, "costo": p_unit_fix})
                                            st.session_state["flash_msg"] = ("success", f"✅ Partida {cp['numero_partida']} corregida con precio ${p_unit_fix:,.2f}.")
                                            st.rerun()
                        with c_fix_col2:
                            with st.popover("↩️ Devolver Solicitud a CS-AT"):
                                st.markdown("**Devolución para Re-cotización:**")
                                mot_dev_ui = st.text_area(
                                    "Motivo de devolución a las Áreas Técnicas:",
                                    value="Favor de registrar los costos unitarios del catálogo oficial (la solicitud presenta partidas con costo $0.00).",
                                    key=f"c_mot_dev_ceros_{s['id']}"
                                )
                                if st.button("Confirmar Devolución al Especialista", key=f"c_btn_dev_ceros_{s['id']}", type="primary"):
                                    conn, engine = cdb.get_db_connection()
                                    c = conn.cursor()
                                    c.execute("UPDATE sub_solicitudes_at SET estado = 'DEVUELTA', motivo_devolucion = ? WHERE solicitud_id = ?", (mot_dev_ui, s['id']))
                                    c.execute("UPDATE solicitudes_master SET estado = 'DEVUELTA' WHERE id = ?", (s['id'],))
                                    conn.commit()
                                    conn.close()
                                    cdb.log_auditoria(user['correo'], "DEVOLVER_SOLICITUD", "SOLICITUD_MASTER", s['id'], {"motivo": mot_dev_ui})
                                    st.session_state["flash_msg"] = ("warning", f"↩️ Solicitud **{s['no_solicitud']}** devuelta a CS-AT para corrección de costos.")
                                    st.rerun()
                    
                    col_c1, col_c2, col_c3 = st.columns([2, 2, 3])
                    with col_c1:
                        if not s['no_cotizacion'] and is_ready:
                            if hay_ceros:
                                st.button("🏷️ Asignar No. Cotización (Bloqueado por Precios $0.00)", disabled=True, key=f"c_dis_cot_{s['id']}")
                            else:
                                next_cot = cdb.get_next_cotizacion_number()
                                if st.button(f"🏷️ Asignar No. Cotización ({next_cot})", key=f"cot_c_{s['id']}"):
                                    conn, engine = cdb.get_db_connection()
                                    c = conn.cursor()
                                    c.execute("""
                                    UPDATE solicitudes_master
                                    SET no_cotizacion = ?, estado = 'EMITIDA', fecha_emision = ?
                                    WHERE id = ?
                                    """, (next_cot, datetime.now().strftime("%Y-%m-%d"), s['id']))
                                    conn.commit()
                                    conn.close()
                                    cdb.log_auditoria(user['correo'], "EMITIR_COTIZACION", "SOLICITUD_MASTER", s['id'], {"no_cotizacion": next_cot})
                                    st.session_state["flash_msg"] = ("success", f"🏷️ No. de Cotización **{next_cot}** asignado con éxito.")
                                    st.rerun()
                        elif s['no_cotizacion']:
                            st.success(f"No. Cotización: **{s['no_cotizacion']}**")
                            
                    with col_c2:
                        os.makedirs("generated_docs", exist_ok=True)
                        if has_viable and s['no_cotizacion'] and not hay_ceros:
                            f_pdf = f"generated_docs/Cotizacion_Cloud_{s['no_folio'].replace('-', '_')}_{s['no_cotizacion']}.pdf"
                            pdf_gen.generate_cotizacion_pdf(dict(s), [dict(p) for p in parts], f_pdf)
                            with open(f_pdf, "rb") as f:
                                st.download_button("📥 Descargar Cotización PDF", f, file_name=f"Cotizacion_{s['no_folio']}.pdf", key=f"dl_c_{s['id']}")
                        if has_dsnr:
                            f_dsnr = f"generated_docs/DSNR_Cloud_{s['no_folio'].replace('-', '_')}.pdf"
                            pdf_gen.generate_dsnr_pdf(dict(s), [dict(p) for p in parts if p['es_no_realizable']==1], "Dirección de Metrología", f_dsnr)
                            with open(f_dsnr, "rb") as f:
                                st.download_button("📄 Descargar DSNR PR PDF", f, file_name=f"DSNR_PR_{s['no_folio']}.pdf", key=f"dl_d_{s['id']}")

                    with col_c3:
                        if (s['no_cotizacion'] and not hay_ceros) or (not has_viable and has_dsnr):
                            with st.popover("✉️ Enviar Cotización al Cliente"):
                                st.markdown(f"**Destinatario:** `{s['correo']}`")
                                asunto_mail = f"CENAM - Cotizacion Oficial Folio {s['no_folio']} / Solicitud {s['no_solicitud']}"
                                cuerpo_mail = f"Estimado(a) {s['representante'] or s['cliente']}:%0D%0A%0D%0APor medio de la presente, el Centro Nacional de Metrologia (CENAM) hace entrega formal de la Cotizacion No. {s['no_cotizacion'] or ''} correspondiente a su solicitud con Folio {s['no_folio']}.%0D%0A%0D%0AFavor de revisar el documento PDF adjunto y regresar el formato con las partidas aceptadas marcadas.%0D%0A%0D%0AAtentamente,%0D%0AVentanilla Central de Servicios (SSI)%0D%0ACENAM"
                                mailto_url = f"mailto:{s['correo']}?subject={asunto_mail}&body={cuerpo_mail}"
                                st.markdown(f"[📬 Abrir Correo con Plantilla Oficial]({mailto_url})")
                                if st.button("🚀 Confirmar Envío al Cliente y Pasar a Programación", key=f"btn_send_c_{s['id']}", type="primary"):
                                    conn, engine = cdb.get_db_connection()
                                    c = conn.cursor()
                                    c.execute("UPDATE solicitudes_master SET estado = 'COTIZACION_ENVIADA' WHERE id = ?", (s['id'],))
                                    conn.commit()
                                    conn.close()
                                    cdb.log_auditoria(user['correo'], "ENVIAR_COTIZACION", "SOLICITUD_MASTER", s['id'], {"folio": s['no_folio']})
                                    st.session_state["flash_msg"] = ("success", f"✅ Cotización Folio **{s['no_folio']}** enviada al cliente. Pasa a la fase de Aceptación y Programación.")
                                    st.rerun()

    # TAB 4: ACEPTACIÓN Y PROGRAMACIÓN POR AT
    with t4:
        st.subheader("Gestión de Aceptación y Programación de Fechas por Área Técnica (CS-AT)")
        conn, engine = cdb.get_db_connection()
        c = conn.cursor()
        c.execute("""
            SELECT m.*, COUNT(s.id) as total_subs
            FROM solicitudes_master m
            LEFT JOIN sub_solicitudes_at s ON m.id = s.solicitud_id
            WHERE m.estado IN ('COTIZACION_ENVIADA', 'COTIZACION_ACEPTADA', 'EN_PROGRAMACION', 'PROGRAMA_PROPUESTO', 'REPROGRAMACION')
            GROUP BY m.id
            ORDER BY m.id DESC
        """)
        sol_prog = c.fetchall()
        
        # OPTIMIZACIÓN SUPABASE: Batch queries para Tab 4 (evita consultas anidadas N+1)
        sol_ids = [s['id'] for s in sol_prog]
        subs_by_sol = {sid: [] for sid in sol_ids}
        parts_by_sol = {sid: [] for sid in sol_ids}
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
                parts_by_sol[p_dict['solicitud_id']].append(p_dict)
                sub_id = p_dict.get('sub_solicitud_id')
                if sub_id:
                    if sub_id not in parts_by_sub:
                        parts_by_sub[sub_id] = []
                    parts_by_sub[sub_id].append(p_dict)
        conn.close()
        
        if not sol_prog:
            st.info("No hay solicitudes activas en fase de aceptación o programación.")
        else:
            for s in sol_prog:
                st_badge = "📬 Esperando Aceptación del Cliente" if s['estado'] == 'COTIZACION_ENVIADA' else f"🗓️ En Programación ({s['estado']})"
                with st.expander(f"Folio: {s['no_folio']} | Cotización: {s['no_cotizacion']} | {s['cliente']} [{st_badge}]", expanded=True):
                    if s['estado'] == 'COTIZACION_ENVIADA':
                        st.markdown("#### Aceptación de Partidas por el Cliente")
                        col_oc1, col_oc2 = st.columns(2)
                        with col_oc1:
                            oc_val = st.text_input("📄 No. de Orden de Compra u Oficio de Aceptación:", value=s.get('orden_compra_cliente') or "", key=f"c_oc_{s['id']}", placeholder="Ej. OC-2026-0812 / OF-CLI-554")
                        with col_oc2:
                            f_acep = st.date_input("📅 Fecha de Aceptación por el Cliente:", value=date.today(), key=f"c_facep_{s['id']}")
                            
                        # Datos desde memoria (Batch Query, 0 consultas a BD)
                        pts = [p for p in parts_by_sol.get(s['id'], []) if p['es_no_realizable'] == 0]
                        
                        st.caption("Seleccione las partidas que el cliente autorizó para calibrar. Las partidas desmarcadas quedarán registradas como DECLINADA_POR_CLIENTE:")
                        
                        partidas_sel = {}
                        subtot_acep = 0.0
                        for p in pts:
                            cant_p = int(p.get('cantidad') or 1)
                            p_unit = float(p.get('precio_unitario') or 0.0)
                            p_tot = float(p.get('precio_total') or (p_unit * cant_p))
                            
                            c_box1, c_box2 = st.columns([4, 1])
                            with c_box1:
                                label_chk = f"**Partida {p['numero_partida']}:** {p['descripcion_equipo']} [{p.get('marca') or ''} {p.get('modelo') or ''}] — *{p.get('descripcion_servicio') or ''}*"
                                is_chk = st.checkbox(label_chk, value=True, key=f"c_chk_acep_{p['id']}")
                                partidas_sel[p['id']] = is_chk
                                if p.get('comentarios_cliente'):
                                    st.caption(f"📋 *Condiciones cotizadas:* {p['comentarios_cliente']}")
                            with c_box2:
                                st.markdown(f"**${p_tot:,.2f}**\n\n({cant_p} serv. a ${p_unit:,.2f})")
                            st.divider()
                            
                            if is_chk:
                                subtot_acep += p_tot
                                
                        iva_acep = subtot_acep * 0.16 if s['aplica_iva'] else 0.0
                        tot_acep = subtot_acep + iva_acep
                        
                        c_ac1, c_ac2, c_ac3 = st.columns(3)
                        with c_ac1:
                            st.metric("Subtotal Aceptado", f"${subtot_acep:,.2f}")
                        with c_ac2:
                            st.metric("IVA (16%) Aceptado", f"${iva_acep:,.2f}" if s['aplica_iva'] else "$0.00 (Exento)")
                        with c_ac3:
                            st.metric("Total General Aceptado", f"${tot_acep:,.2f}")
                            
                        n_acep = sum(1 for v in partidas_sel.values() if v)
                        n_decl = len(partidas_sel) - n_acep
                        st.info(f"📊 Resumen de selección: **{n_acep} partida(s) aceptada(s)** y **{n_decl} partida(s) declinada(s)**.")
                        
                        if st.button("🚀 Confirmar Aceptación y Turnar a Programación con CS-AT", key=f"c_btn_turn_prog_{s['id']}", type="primary"):
                            if n_acep == 0:
                                st.error("Debe seleccionar al menos una partida aceptada para turnar a programación.")
                            else:
                                conn, engine = cdb.get_db_connection()
                                c = conn.cursor()
                                # Actualizar partidas aceptadas y declinadas
                                for pid, aceptada in partidas_sel.items():
                                    st_p = 'ACEPTADA' if aceptada else 'DECLINADA_POR_CLIENTE'
                                    c.execute("UPDATE partidas SET aceptada_cliente = ?, estado_partida = ? WHERE id = ?", (1 if aceptada else 0, st_p, pid))
                                    
                                # Actualizar solicitud master
                                c.execute("""
                                    UPDATE solicitudes_master
                                    SET estado = 'EN_PROGRAMACION', fecha_aceptacion_cotizacion = ?, orden_compra_cliente = ?
                                    WHERE id = ?
                                """, (f_acep.strftime("%Y-%m-%d"), oc_val, s['id']))
                                
                                # Turnar a las ATs que sí tienen partidas aceptadas
                                c.execute("""
                                    UPDATE sub_solicitudes_at
                                    SET estado = 'EN_PROGRAMACION'
                                    WHERE solicitud_id = ?
                                      AND id IN (SELECT sub_solicitud_id FROM partidas WHERE solicitud_id = ? AND aceptada_cliente = 1)
                                """, (s['id'], s['id']))
                                
                                # Cancelar sub_solicitudes donde NO hubo ninguna partida aceptada
                                c.execute("""
                                    UPDATE sub_solicitudes_at
                                    SET estado = 'CANCELADA_CLIENTE'
                                    WHERE solicitud_id = ?
                                      AND id NOT IN (SELECT sub_solicitud_id FROM partidas WHERE solicitud_id = ? AND aceptada_cliente = 1)
                                """, (s['id'], s['id']))
                                
                                conn.commit()
                                conn.close()
                                cdb.log_auditoria(user['correo'], "ACEPTAR_COTIZACION", "SOLICITUD_MASTER", s['id'], {
                                    "folio": s['no_folio'],
                                    "orden_compra": oc_val,
                                    "aceptadas": n_acep,
                                    "declinadas": n_decl,
                                    "total_aceptado": tot_acep
                                })
                                st.session_state["flash_msg"] = ("success", f"📅 Cotización Folio **{s['no_folio']}** aceptada ({n_acep} partidas). Se turnó a programación con CS-AT.")
                                st.rerun()
                    else:
                        st.markdown("#### Propuestas de Programación de Fechas por Área Técnica")
                        # Datos desde memoria (Batch Query, 0 consultas a BD)
                        subs_prog = subs_by_sol.get(s['id'], [])
                        
                        for sub in subs_prog:
                            st.markdown(f"**Área Técnica:** `{sub['clave_area']}` - **{sub['nombre_area']}** | Estado: `{sub['estado']}`")
                            sub_parts = [p for p in parts_by_sub.get(sub['id'], []) if p.get('aceptada_cliente') == 1]
                            
                            if sub_parts:
                                p_df = pd.DataFrame([{
                                    "Part.": p['numero_partida'],
                                    "Servicio": p['descripcion_servicio'],
                                    "Recepción Equipo (9:00-16:30)": p['fecha_recepcion_equipo'] or sub['fecha_recepcion_prog'] or 'Pendiente AT',
                                    "Inicio Calibración": p['fecha_inicio_calibracion'] or sub['fecha_inicio_prog'] or 'Pendiente AT',
                                    "Entrega / Fin": p['fecha_entrega_equipo'] or sub['fecha_entrega_prog'] or 'Pendiente AT',
                                    "Límite Aceptación": p['fecha_limite_aceptacion'] or sub['fecha_limite_prog'] or '3 semanas'
                                } for p in sub_parts])
                                st.dataframe(p_df, width="stretch")
                                
                                if sub['estado'] in ('PROGRAMA_PROPUESTO', 'PROGRAMA_CONFIRMADO'):
                                    col_p1, col_p2, col_p3 = st.columns([2, 2, 3])
                                    with col_p1:
                                        os.makedirs("generated_docs", exist_ok=True)
                                        prog_pdf_path = f"generated_docs/Programacion_Cloud_{s['no_folio'].replace('-', '_')}_{sub['clave_area']}.pdf"
                                        sol_dict = dict(s)
                                        sub_dict = dict(sub)
                                        parts_list = [dict(p) for p in sub_parts]
                                        tipo_prog = 'IN_SITU' if s['es_in_situ'] else 'CENAM'
                                        pdf_gen.generate_programacion_pdf(sol_dict, sub_dict, parts_list, tipo=tipo_prog, filepath=prog_pdf_path)
                                        with open(prog_pdf_path, "rb") as f:
                                            st.download_button(
                                                f"📄 Descargar Programación PDF ({sub['clave_area']})",
                                                data=f,
                                                file_name=f"Programacion_{s['no_folio']}_{sub['clave_area']}.pdf",
                                                mime="application/pdf",
                                                key=f"c_dl_prog_{sub['id']}"
                                            )
                                    with col_p2:
                                        with st.popover("✉️ Enviar Propuesta de Fechas"):
                                            st.markdown(f"**Destinatario:** `{s['correo']}`")
                                            asunto_p = f"CENAM - Propuesta de Programacion {sub['clave_area']} Folio {s['no_folio']}"
                                            body_p = f"Estimado(a) {s['representante'] or s['cliente']}:%0D%0A%0D%0ALe informamos las fechas programadas para los servicios de calibracion del Area Tecnica {sub['clave_area']}.%0D%0A%0D%0AFavor de revisar el documento de Programacion adjunto para su aceptacion.%0D%0A%0D%0AAtentamente,%0D%0ACoordinador de Servicios (SSI) - CENAM"
                                            mailto_prog = f"mailto:{s['correo']}?subject={asunto_p}&body={body_p}"
                                            st.markdown(f"[📬 Abrir Correo con Propuesta]({mailto_prog})")
                                            if st.button("Confirmar Envío", key=f"c_btn_send_p_{sub['id']}"):
                                                st.toast(f"Propuesta enviada al cliente", icon="✉️")
                                    with col_p3:
                                        with st.popover("🔄 Solicitar Cambio de Fecha (Reprogramación)"):
                                            st.markdown("**Solicitud de Reprogramación hacia CS-AT**")
                                            motivo_rep = st.text_area("Indique fechas solicitadas por el cliente:", key=f"c_mot_rep_{sub['id']}")
                                            if st.button("Turnar a CS-AT", key=f"c_btn_turn_rep_{sub['id']}"):
                                                conn, engine = cdb.get_db_connection()
                                                c = conn.cursor()
                                                c.execute("UPDATE sub_solicitudes_at SET estado = 'REPROGRAMACION', motivo_reprogramacion = ? WHERE id = ?", (motivo_rep, sub['id']))
                                                c.execute("UPDATE solicitudes_master SET estado = 'REPROGRAMACION' WHERE id = ?", (s['id'],))
                                                conn.commit()
                                                conn.close()
                                                cdb.log_auditoria(user['correo'], "SOLICITAR_REPROGRAMACION", "SUB_SOLICITUD", sub['id'], {"motivo": motivo_rep})
                                                st.session_state["flash_msg"] = ("warning", f"🔄 Sub-solicitud turnada al CS-AT de {sub['clave_area']} para reprogramación.")
                                                st.rerun()
                            st.write("")
                            
                        todos_listos = all(sub['estado'] in ('PROGRAMA_PROPUESTO', 'PROGRAMA_CONFIRMADO') for sub in subs_prog)
                        if todos_listos:
                            if st.button("🎉 Cliente Aceptó Programación -> Formalizar Contratos", key=f"c_btn_goto_conf_{s['id']}", type="primary"):
                                conn, engine = cdb.get_db_connection()
                                c = conn.cursor()
                                c.execute("UPDATE solicitudes_master SET estado = 'PROGRAMA_CONFIRMADO' WHERE id = ?", (s['id'],))
                                conn.commit()
                                conn.close()
                                st.session_state["flash_msg"] = ("success", f"📜 Folio {s['no_folio']} listo para formalizar contrato.")
                                st.rerun()

    # TAB 5: CONFIRMACIÓN Y CONTRATOS
    with t5:
        st.subheader("Formalización de Contratos, Retorno de Equipos y Confirmación Definitiva")
        conn, engine = cdb.get_db_connection()
        c = conn.cursor()
        c.execute("SELECT * FROM solicitudes_master WHERE estado IN ('PROGRAMA_CONFIRMADO', 'CONFIRMADA_CONCLUIDA') ORDER BY id DESC")
        sol_conf = c.fetchall()
        
        # OPTIMIZACIÓN SUPABASE: Batch queries para Tab 5
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
        
        if not sol_conf:
            st.info("No hay solicitudes pendientes de formalizar contrato.")
        else:
            for s in sol_conf:
                is_concluida = (s['estado'] == 'CONFIRMADA_CONCLUIDA')
                tag = "🏁 SERVICIO CONFIRMADO Y CONTRATO FORMALIZADO" if is_concluida else "📋 PENDIENTE DE FORMALIZAR"
                with st.expander(f"Folio: {s['no_folio']} | Cotización: {s['no_cotizacion']} | {s['cliente']} [{tag}]", expanded=not is_concluida):
                    c_conf1, c_conf2 = st.columns(2)
                    with c_conf1:
                        st.markdown("#### Configuración de Contrato y Retorno de Equipos")
                        ret_actual = s['modalidad_retorno'] or 'RECOLECCION_CENAM'
                        opciones_ret = {
                            'RECOLECCION_CENAM': 'Opción 1: Mi empresa recogerá el equipo en instalaciones del CENAM',
                            'MENSAJERIA_CLIENTE': 'Opción 2: Mi empresa contratará servicio de mensajería para recolección',
                            'GUIA_PREPAGADA': 'Opción 3: Mi empresa enviará una guía prepagada para el retorno'
                        }
                        nueva_ret = st.radio("Modalidad de Retorno de Equipo:", options=list(opciones_ret.keys()), format_func=lambda x: opciones_ret[x], index=list(opciones_ret.keys()).index(ret_actual), key=f"c_ret_{s['id']}")
                        rep_cenam_actual = s['representante_legal_cenam'] or ""
                        rep_cenam_input = st.text_input("Representante Legal del CENAM (Dejar vacío para firma autógrafa física):", value=rep_cenam_actual, placeholder="Ej. Lic. Nombre del Representante Legal (o en blanco)", key=f"c_rep_{s['id']}")
                        
                        if s['es_in_situ']:
                            dir_planta = st.text_input("Dirección de la planta donde se realizará el servicio:", value=s['direccion_servicio_sitio'] or "", key=f"c_dir_{s['id']}")
                            cond_planta = st.text_input("Condiciones de acceso a planta (EPP, inducción):", value=s['condiciones_acceso_planta'] or "Equipo de protección personal completo", key=f"c_cond_{s['id']}")
                        else:
                            dir_planta = None
                            cond_planta = None
                    with c_conf2:
                        st.markdown("#### Descarga de Contratos y Programaciones por AT")
                        # Datos desde memoria (Batch Query, 0 consultas a BD)
                        subs = subs_by_conf.get(s['id'], [])
                        
                        for sub in subs:
                            parts = parts_by_sub_conf.get(sub['id'], [])
                            if parts:
                                os.makedirs("generated_docs", exist_ok=True)
                                pdf_path = f"generated_docs/Contrato_Programacion_Cloud_{s['no_folio'].replace('-', '_')}_{sub['clave_area']}.pdf"
                                sol_d = dict(s)
                                sol_d['modalidad_retorno'] = nueva_ret
                                sol_d['direccion_servicio_sitio'] = dir_planta
                                sol_d['condiciones_acceso_planta'] = cond_planta
                                pdf_gen.generate_programacion_pdf(sol_d, dict(sub), [dict(p) for p in parts], tipo='IN_SITU' if s['es_in_situ'] else 'CENAM', filepath=pdf_path, rep_legal_cenam=rep_cenam_input)
                                with open(pdf_path, "rb") as f:
                                    st.download_button(f"📜 Descargar Contrato y Programación ({sub['clave_area']})", data=f, file_name=f"Contrato_Programacion_{s['no_folio']}_{sub['clave_area']}.pdf", mime="application/pdf", key=f"c_dl_c_{sub['id']}")
                    st.divider()
                    if not is_concluida:
                        if st.button("🏁 Confirmar Servicio, Reservar Laboratorios y Archivar Trámite", key=f"c_btn_fin_all_{s['id']}", type="primary"):
                            if parts:
                                os.makedirs("generated_docs", exist_ok=True)
                                pdf_path = f"generated_docs/Contrato_Programacion_Cloud_{s['no_folio'].replace('-', '_')}_{sub['clave_area']}.pdf"
                                sol_d = dict(s)
                                sol_d['modalidad_retorno'] = nueva_ret
                                sol_d['direccion_servicio_sitio'] = dir_planta
                                sol_d['condiciones_acceso_planta'] = cond_planta
                                pdf_gen.generate_programacion_pdf(sol_d, dict(sub), [dict(p) for p in parts], tipo='IN_SITU' if s['es_in_situ'] else 'CENAM', filepath=pdf_path, rep_legal_cenam=rep_cenam_input)
                                with open(pdf_path, "rb") as f:
                                    st.download_button(f"📜 Descargar Contrato y Programación ({sub['clave_area']})", data=f, file_name=f"Contrato_Programacion_{s['no_folio']}_{sub['clave_area']}.pdf", mime="application/pdf", key=f"c_dl_c_{sub['id']}")
                    st.divider()
                    if not is_concluida:
                        if st.button("🏁 Confirmar Servicio, Reservar Laboratorios y Archivar Trámite", key=f"c_btn_fin_all_{s['id']}", type="primary"):
                            conn, engine = cdb.get_db_connection()
                            c = conn.cursor()
                            c.execute("""
                            UPDATE solicitudes_master
                            SET estado = 'CONFIRMADA_CONCLUIDA', modalidad_retorno = ?, representante_legal_cenam = ?,
                                direccion_servicio_sitio = ?, condiciones_acceso_planta = ?, fecha_confirmacion_programa = ?
                            WHERE id = ?
                            """, (nueva_ret, rep_cenam_input, dir_planta, cond_planta, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), s['id']))
                            c.execute("UPDATE sub_solicitudes_at SET estado = 'PROGRAMA_CONFIRMADO' WHERE solicitud_id = ?", (s['id'],))
                            conn.commit()
                            conn.close()
                            cdb.log_auditoria(user['correo'], "CONFIRMAR_SERVICIO", "SOLICITUD_MASTER", s['id'], {"folio": s['no_folio']})
                            st.session_state["flash_msg"] = ("success", f"🏁 ¡Servicio confirmado exitosamente! Folio **{s['no_folio']}**. Se ha notificado a los laboratorios CS-AT para la reserva.")
                            st.rerun()

    # TAB 6: AUDITORÍA
    with t6:
        st.subheader("Bitácora de Auditoría Inmutable (Trazabilidad Total ISO 17025)")
        conn, engine = cdb.get_db_connection()
        c = conn.cursor()
        c.execute("SELECT id, usuario_correo, accion, entidad, registro_id, detalles, fecha FROM bitacora_auditoria ORDER BY id DESC LIMIT 100")
        logs = c.fetchall()
        conn.close()
        if logs:
            st.dataframe(pd.DataFrame([dict(l) for l in logs]), width="stretch")
        else:
            st.info("No hay eventos registrados en la bitácora aún.")

        if rol == "ADMIN":
            st.markdown("---")
            st.subheader("🧹 Mantenimiento del Sistema y Depuración Operativa")
            st.caption("Herramienta reservada para administradores: permite reiniciar el sistema operativo a estado cero.")
            
            with st.expander("⚙️ Zona de Reinicio Operativo (Conservar Catálogos y Usuarios)", expanded=False):
                st.warning(
                    "Esta acción eliminará todas las **solicitudes**, **sub-solicitudes**, **programaciones de fechas** y **partidas** registradas.\n\n"
                    "✅ **Garantía de Seguridad:** Los catálogos institucionales (**1,036 servicios**, **294 laboratorios**, **15 direcciones técnicas**) y las cuentas de **usuarios** se conservan 100% intactos.\n\n"
                    "🔄 **Reinicio de Folios:** Las siguientes solicitudes comenzarán nuevamente desde el Folio `0001-2026PR` y Solicitud `2026001PR`."
                )
                c_maint1, c_maint2 = st.columns([3, 2])
                with c_maint1:
                    limp_audit_ui = st.checkbox("Limpiar también eventos de prueba en la bitácora de auditoría", value=True, key="c_chk_audit_maint")
                with c_maint2:
                    with st.popover("🚨 Confirmar Limpieza Operativa"):
                        st.error("¿Confirma la depuración de todas las solicitudes y programaciones de prueba?")
                        if st.button("Confirmar y Limpiar Base Operativa", type="primary", key="c_btn_purge_operativa"):
                            eliminados = cdb.limpiar_solicitudes_y_programaciones(limpiar_auditoria=limp_audit_ui)
                            st.session_state["flash_msg"] = ("success", f"🧹 Base de datos depurada exitosamente. Registros eliminados: {eliminados}. Folios reiniciados a cero.")
                            st.rerun()

# ==========================================
# VISTA 2: ROL ÁREA TÉCNICA (CS-AT)
# ==========================================
else:
    if rol == "ADMIN":
        at_actual = st.sidebar.selectbox("Seleccione Área a evaluar (Admin):", options=list(areas_dict.keys()), format_func=lambda x: f"{x} - {areas_dict[x]} [{areas_dir_dict.get(x, '')}]" if areas_dir_dict.get(x) else f"{x} - {areas_dict[x]}")
    else:
        at_actual = clave_area

    st.title(f"🔬 {at_actual} - {areas_dict.get(at_actual, '')}")
    if areas_dir_dict.get(at_actual):
        st.caption(f"🏛️ **Dirección General:** {areas_dir_dict.get(at_actual)}")
    st.caption(f"Usuario: {user['nombre_completo']} | Rol: CS-AT (Evaluación, Cotización y Programación)")
    
    col_sla1, col_sla2 = st.columns([3, 2])
    with col_sla2:
        st.info("⏱️ **Reglas de Calidad:** 3 días hábiles para cotizar. La fecha de recepción se calcula automáticamente a 2 días hábiles antes de la fecha de inicio.")
    
    at_tab1, at_tab2, at_tab3 = st.tabs(["🔬 1. Cotización Metrológica", "🗓️ 2. Programación de Fechas", "📌 3. Calendario Confirmado"])
    
    # AT PESTAÑA 1: COTIZACIÓN
    with at_tab1:
        conn, engine = cdb.get_db_connection()
        c = conn.cursor()
        c.execute("""
            SELECT s.id as sub_id, m.id as master_id, m.no_folio, m.no_solicitud, m.cliente,
                   m.representante, s.estado, s.fecha_asignacion, s.fecha_limite_sla, m.es_in_situ
            FROM sub_solicitudes_at s
            JOIN solicitudes_master m ON s.solicitud_id = m.id
            WHERE s.clave_area = ? AND s.estado IN ('ASIGNADA', 'EN_CONSULTA')
            ORDER BY s.id DESC
        """, (at_actual,))
        solicitudes_at = c.fetchall()
        conn.close()
        
        if len(solicitudes_at) > 0:
            st.info(f"🔔 **Aviso CS-AT ({at_actual}):** Tiene **{len(solicitudes_at)} solicitud(es) pendiente(s)** de cotización.", icon="🔔")
        
        if not solicitudes_at:
            st.success(f"🎉 No hay cotizaciones pendientes para **{at_actual}**. ¡Bandeja al día!")
        else:
            for sol in solicitudes_at:
                sla_text = get_sla_badge(sol['fecha_asignacion'])
                mod_label = "🚗 IN SITU (Viáticos)" if sol['es_in_situ'] else "🔬 LAB CENAM"
                with st.expander(f"📋 Folio: {sol['no_folio']} | Solicitud: {sol['no_solicitud']} [{mod_label}] | Cliente: {sol['cliente']} | SLA: {sla_text}", expanded=True):
                    st.markdown(f"**Modalidad Operativa:** `{mod_label}` | **División:** `{at_actual}` - {areas_dict.get(at_actual, '')}")
                    c_act1, c_act2, c_act3 = st.columns(3)
                    with c_act1:
                        with st.popover("↩️ Devolver a SSI (No Corresponde a mi Área)"):
                            st.markdown("**Devolución inmediata a SSI sin cotizar**")
                            mot_d = st.text_area("Motivo técnico:", key=f"c_mot_{sol['sub_id']}")
                            sug_at = st.selectbox("Área sugerida:", options=[a for a in areas_dict.keys() if a != at_actual], format_func=lambda x: f"{x} - {areas_dict[x]} [{areas_dir_dict.get(x, '')}]" if areas_dir_dict.get(x) else f"{x} - {areas_dict[x]}", key=f"c_sug_{sol['sub_id']}")
                            if st.button("Confirmar Devolución", key=f"c_btn_dev_{sol['sub_id']}"):
                                conn, engine = cdb.get_db_connection()
                                c = conn.cursor()
                                c.execute("UPDATE sub_solicitudes_at SET estado = 'DEVUELTA', motivo_devolucion = ?, area_sugerida = ? WHERE id = ?", (mot_d, sug_at, sol['sub_id']))
                                conn.commit()
                                conn.close()
                                cdb.log_auditoria(user['correo'], "DEVOLVER_SOLICITUD", "SUB_SOLICITUD", sol['sub_id'], {"folio": sol['no_folio'], "motivo": mot_d})
                                st.session_state["flash_msg"] = ("warning", f"↩️ Solicitud Folio **{sol['no_folio']}** devuelta a SSI para reasignación.")
                                st.rerun()
                    with c_act2:
                        with st.popover("👨‍🔬 Consultar Especialista (SLA 3 Días)"):
                            esp_name = st.text_input("Nombre Especialista:", key=f"c_esp_{sol['sub_id']}")
                            esp_preg = st.text_area("Pregunta Metrológica:", key=f"c_preg_{sol['sub_id']}")
                            esp_resp = st.text_area("Respuesta del Especialista (ISO 17025):", key=f"c_resp_{sol['sub_id']}")
                            if st.button("Guardar Evidencia", key=f"c_btn_save_esp_{sol['sub_id']}"):
                                conn, engine = cdb.get_db_connection()
                                c = conn.cursor()
                                c.execute("""
                                INSERT INTO consultas_especialistas (sub_solicitud_id, especialista_nombre, pregunta, respuesta, fecha_consulta, fecha_respuesta, estado)
                                VALUES (?, ?, ?, ?, ?, ?, 'CONTESTADA')
                                """, (sol['sub_id'], esp_name, esp_preg, esp_resp, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                                c.execute("UPDATE sub_solicitudes_at SET estado = 'EN_CONSULTA' WHERE id = ?", (sol['sub_id'],))
                                conn.commit()
                                conn.close()
                                cdb.log_auditoria(user['correo'], "CONSULTA_ESPECIALISTA", "SUB_SOLICITUD", sol['sub_id'], {"especialista": esp_name})
                                st.success("Evidencia archivada con éxito.")
                                st.rerun()
                    with c_act3:
                        if not sol['es_in_situ']:
                            with st.popover("🚗 Separar Partidas a Solicitud IN SITU"):
                                st.markdown("##### Segregar Partidas a Modalidad IN SITU")
                                st.caption("Seleccione las partidas que deban realizarse en planta del cliente con viáticos. Se generará una nueva Solicitud bajo el mismo Folio.")
                                
                                conn_temp, _ = cdb.get_db_connection()
                                c_temp = conn_temp.cursor()
                                c_temp.execute("SELECT id, numero_partida, descripcion_equipo FROM partidas WHERE sub_solicitud_id = ? ORDER BY numero_partida", (sol['sub_id'],))
                                parts_temp = c_temp.fetchall()
                                conn_temp.close()
                                
                                sel_to_sep = []
                                for pt in parts_temp:
                                    chk_s = st.checkbox(f"Partida {pt['numero_partida']}: {pt['descripcion_equipo']}", key=f"c_chk_sep_{pt['id']}")
                                    if chk_s:
                                        sel_to_sep.append(pt['id'])
                                        
                                if st.button("🚀 Confirmar Separación IN SITU", key=f"c_btn_sep_{sol['sub_id']}", type="primary"):
                                    if not sel_to_sep:
                                        st.warning("Seleccione al menos una partida para separar.")
                                    else:
                                        res_sep = cdb.separar_partidas_in_situ(sol['master_id'], sel_to_sep, user['correo'])
                                        st.session_state["flash_msg"] = ("success", f"🚗 Se ha generado la nueva Solicitud IN SITU **{res_sep['nuevo_no_solicitud']}** bajo el Folio **{res_sep['no_folio']}**.")
                                        st.toast(f"Solicitud {res_sep['nuevo_no_solicitud']} creada", icon="🚗")
                                        st.rerun()
                        else:
                            st.info("🚗 Modalidad **IN SITU** (con viáticos)")
                                
                    st.markdown("---")
                    st.markdown("### Partidas Asignadas para Cotización")
                    conn, engine = cdb.get_db_connection()
                    c = conn.cursor()
                    c.execute("SELECT * FROM partidas WHERE sub_solicitud_id = ? ORDER BY numero_partida", (sol['sub_id'],))
                    partidas = c.fetchall()
                    conn.close()
                    # Catálogo en RAM (0 consultas de red a Supabase)
                    servicios_area = serv_by_area.get(str(at_actual), [])
                    labs_disponibles = sorted(list(set(s['codigo_laboratorio'] for s in servicios_area if s.get('codigo_laboratorio'))))
                    
                    for p in partidas:
                        st.markdown(f"**Partida {p['numero_partida']}: {p['descripcion_equipo']}**")
                        st.caption(f"Marca: `{p['marca']}` | Modelo: `{p['modelo']}` | Serie: `{p['no_serie']}` | ID Interno: `{p['id_interno']}` | Cert. anterior: `{p['certificado_anterior'] or 'N/A'}`")
                        
                        col_p1, col_p2, col_p3 = st.columns([4, 2, 2])
                        with col_p1:
                            modo_p = st.radio("Modalidad:", ["Catálogo Oficial de mi Área", "Partida Manual Libre", "Servicio No Realizable (DSNR)"], horizontal=True, key=f"c_modop_{p['id']}")
                            if modo_p == "Catálogo Oficial de mi Área":
                                if not servicios_area:
                                    st.warning("No hay servicios catalogados para esta área.")
                                    s_sel = None
                                    p_costo = 0.0
                                    p_dias = 5
                                    desc_fin = ""
                                else:
                                    if len(labs_disponibles) > 1:
                                        filtro_lab = st.selectbox(
                                            "🔬 Filtrar por Laboratorio:",
                                            options=["(Todos los laboratorios)"] + labs_disponibles,
                                            key=f"c_flab_{p['id']}"
                                        )
                                        if filtro_lab != "(Todos los laboratorios)":
                                            servs_filtrados = [s for s in servicios_area if s.get('codigo_laboratorio') == filtro_lab]
                                        else:
                                            servs_filtrados = servicios_area
                                    else:
                                        servs_filtrados = servicios_area
                                        
                                    serv_map = {
                                        s['clave_servicio']: f"[{s.get('codigo_laboratorio') or 'GRAL'}] {s['clave_servicio']} - {s['supuesto'][:70]}... (${float(s['costo']):,.2f})"
                                        for s in servs_filtrados
                                    }
                                    def_idx = 0
                                    if p.get('clave_servicio') in serv_map:
                                        def_idx = list(serv_map.keys()).index(p['clave_servicio'])
                                    s_sel = st.selectbox("Servicio del Catálogo:", options=list(serv_map.keys()), index=def_idx, format_func=lambda x: serv_map[x], key=f"c_ssel_{p['id']}")
                                    s_obj = next((s for s in servs_filtrados if s['clave_servicio'] == s_sel), None)
                                    p_costo = float(s_obj['costo']) if s_obj else 0.0
                                    p_dias = s_obj['dias_habiles_defecto'] if s_obj else 5
                                    desc_fin = s_obj['supuesto'] if s_obj else ""
                                    if s_obj and s_obj.get('nombre_laboratorio'):
                                        st.caption(f"🏢 **Laboratorio:** `{s_obj.get('codigo_laboratorio', '')}` - {s_obj.get('nombre_laboratorio', '')}")
                                motivo_d = None
                                es_no = 0
                                es_man = 0
                            elif modo_p == "Partida Manual Libre":
                                desc_fin = st.text_input("Descripción personalizada:", value=p['descripcion_servicio'] or "", key=f"c_mdesc_{p['id']}")
                                p_costo = st.number_input("Precio Unitario ($ M.N.):", value=float(p['precio_unitario'] or 0.0), key=f"c_mcost_{p['id']}")
                                p_dias = 5
                                s_sel = "MANUAL"
                                motivo_d = None
                                es_no = 0
                                es_man = 1
                            else:
                                s_sel = "DSNR"
                                desc_fin = p['descripcion_equipo']
                                p_costo = 0.0
                                p_dias = 0
                                es_no = 1
                                es_man = 0
                                motivo_d = st.text_area("Motivo DSNR y Canalización:", value="Lamentamos informarle que este servicio no se realiza en el CENAM. Favor de canalizar este servicio a laboratorios secundarios, actualmente hay muchos que están acreditados.", key=f"c_dsnrtxt_{p['id']}")

                        with col_p2:
                            if es_no == 0:
                                cant = st.number_input("Cantidad de Servicios:", min_value=1, value=int(p['cantidad'] or 1), key=f"c_cant_{p['id']}")
                                dias_c = st.number_input("Días Hábiles (Tiempo cal.):", min_value=1, value=int(p['tiempo_dias_habiles'] or p_dias), key=f"c_dias_{p['id']}")
                            else:
                                cant = 1
                                dias_c = 0
                        with col_p3:
                            tot = p_costo * cant
                            if es_no == 0:
                                st.metric("Costo Total Partida", f"${tot:,.2f}")
                                st.caption(f"Unitario: ${p_costo:,.2f} × {cant}")
                            else:
                                st.error("No Realizable (DSNR)")
                                
                        if es_no == 0:
                            col_com1, col_com2 = st.columns(2)
                            with col_com1:
                                com_ssi = st.text_area("🔒 Comentarios para SSI (Interno - No visible para el cliente):", value=p.get('comentarios_ssi') or "", key=f"c_cssi_{p['id']}", placeholder="Observaciones técnicas de viabilidad o notas operativas para SSI...")
                            with col_com2:
                                com_cli = st.text_area("📋 Comentarios para Cliente (Visible en Cotización oficial):", value=p.get('comentarios_cliente') or "", key=f"c_ccli_{p['id']}", placeholder="Condiciones específicas del servicio que se imprimirán en el PDF para el cliente...")
                        else:
                            com_ssi = ""
                            com_cli = ""
                            
                        if st.button("💾 Guardar Partida", key=f"c_savep_{p['id']}"):
                            conn, engine = cdb.get_db_connection()
                            c = conn.cursor()
                            c.execute("""
                            UPDATE partidas
                            SET es_manual = ?, clave_servicio = ?, descripcion_servicio = ?,
                                tiempo_dias_habiles = ?, cantidad = ?, precio_unitario = ?,
                                precio_total = ?, es_no_realizable = ?, motivo_dsnr = ?,
                                comentarios_ssi = ?, comentarios_cliente = ?, estado_partida = 'COTIZADA'
                            WHERE id = ?
                            """, (es_man, s_sel, desc_fin, dias_c, cant, p_costo, tot, es_no, motivo_d, com_ssi, com_cli, p['id']))
                            conn.commit()
                            conn.close()
                            cdb.log_auditoria(user['correo'], "ACTUALIZAR_PARTIDA", "PARTIDA", p['id'], {"servicio": s_sel, "cantidad": cant, "unitario": p_costo, "total": tot})
                            st.success("Partida guardada con éxito.")
                            st.rerun()
                        st.divider()

                    if st.button("🏁 Aprobar y Regresar Cotización a SSI", key=f"c_fin_{sol['sub_id']}", type="primary"):
                        conn, engine = cdb.get_db_connection()
                        c = conn.cursor()
                        
                        errores_validacion = []
                        
                        # 1. AUTO-GUARDADO Y VALIDACIÓN ESTRICTA DE PRECIOS > 0
                        for p in partidas:
                            pid = p['id']
                            modo_k = f"c_modop_{pid}"
                            modo_val = st.session_state.get(modo_k, "Catálogo Oficial de mi Área" if p.get('clave_servicio') not in ('MANUAL', 'DSNR') else ("Partida Manual Libre" if p.get('es_manual') == 1 else "Servicio No Realizable (DSNR)"))
                            
                            if modo_val == "Catálogo Oficial de mi Área":
                                ssel_k = f"c_ssel_{pid}"
                                s_sel_val = st.session_state.get(ssel_k, p.get('clave_servicio'))
                                s_obj = serv_by_clave.get(s_sel_val)
                                p_costo_val = float(s_obj['costo']) if s_obj else float(p.get('precio_unitario') or 0.0)
                                desc_fin_val = s_obj['supuesto'] if s_obj else (p.get('descripcion_servicio') or "")
                                cant_val = int(st.session_state.get(f"c_cant_{pid}", p.get('cantidad') or 1))
                                dias_val = int(st.session_state.get(f"c_dias_{pid}", p.get('tiempo_dias_habiles') or (s_obj['dias_habiles_defecto'] if s_obj else 5)))
                                tot_val = p_costo_val * cant_val
                                es_no_val = 0
                                es_man_val = 0
                                mot_dsnr_val = None
                                
                                if not s_sel_val or s_sel_val not in serv_by_clave:
                                    errores_validacion.append(f"Partida {p['numero_partida']}: No se ha seleccionado un servicio del catálogo.")
                                elif p_costo_val <= 0.0:
                                    errores_validacion.append(f"Partida {p['numero_partida']}: El servicio seleccionado tiene costo $0.00. Debe registrarse un precio mayor a cero.")
                                    
                            elif modo_val == "Partida Manual Libre":
                                desc_fin_val = st.session_state.get(f"c_mdesc_{pid}", p.get('descripcion_servicio') or "").strip()
                                p_costo_val = float(st.session_state.get(f"c_mcost_{pid}", p.get('precio_unitario') or 0.0))
                                cant_val = int(st.session_state.get(f"c_cant_{pid}", p.get('cantidad') or 1))
                                dias_val = int(st.session_state.get(f"c_dias_{pid}", p.get('tiempo_dias_habiles') or 5))
                                tot_val = p_costo_val * cant_val
                                s_sel_val = "MANUAL"
                                es_no_val = 0
                                es_man_val = 1
                                mot_dsnr_val = None
                                
                                if not desc_fin_val:
                                    errores_validacion.append(f"Partida {p['numero_partida']}: En modo manual debe ingresar una descripción.")
                                if p_costo_val <= 0.0:
                                    errores_validacion.append(f"Partida {p['numero_partida']}: El precio unitario manual no puede ser $0.00.")
                            else:
                                # DSNR
                                s_sel_val = "DSNR"
                                desc_fin_val = p['descripcion_equipo']
                                p_costo_val = 0.0
                                cant_val = 1
                                dias_val = 0
                                tot_val = 0.0
                                es_no_val = 1
                                es_man_val = 0
                                mot_dsnr_val = st.session_state.get(f"c_dsnrtxt_{pid}", p.get('motivo_dsnr') or "Lamentamos informarle que este servicio no se realiza en el CENAM.")
                                
                            cssi_val = st.session_state.get(f"c_cssi_{pid}", p.get('comentarios_ssi') or "") if es_no_val == 0 else ""
                            ccli_val = st.session_state.get(f"c_ccli_{pid}", p.get('comentarios_cliente') or "") if es_no_val == 0 else ""
                            
                            c.execute("""
                                UPDATE partidas
                                SET es_manual = ?, clave_servicio = ?, descripcion_servicio = ?,
                                    tiempo_dias_habiles = ?, cantidad = ?, precio_unitario = ?,
                                    precio_total = ?, es_no_realizable = ?, motivo_dsnr = ?,
                                    comentarios_ssi = ?, comentarios_cliente = ?, estado_partida = 'COTIZADA'
                                WHERE id = ?
                            """, (es_man_val, s_sel_val, desc_fin_val, dias_val, cant_val, p_costo_val, tot_val, es_no_val, mot_dsnr_val, cssi_val, ccli_val, pid))
                        
                        conn.commit()
                        
                        if errores_validacion:
                            conn.close()
                            for err in errores_validacion:
                                st.error(f"❌ {err}")
                            st.warning("⚠️ **Cotización NO aprobada:** Corrija las partidas indicadas antes de enviar a SSI. Todos los servicios viables deben tener un precio mayor a $0.00.")
                        else:
                            c.execute("UPDATE sub_solicitudes_at SET estado = 'COMPLETADA' WHERE id = ?", (sol['sub_id'],))
                            conn.commit()
                            conn.close()
                            cdb.log_auditoria(user['correo'], "COMPLETAR_SUB_SOLICITUD", "SUB_SOLICITUD", sol['sub_id'], {"folio": sol['no_folio']})
                            st.session_state["flash_msg"] = ("success", f"✅ ¡Cotización Folio **{sol['no_folio']}** guardada y aprobada hacia SSI con éxito! (Precios y partidas validados).")
                            st.rerun()

    # AT PESTAÑA 2: PROGRAMACIÓN DE FECHAS
    with at_tab2:
        st.subheader("Programación de Fechas de Laboratorio (Servicios con Cotización Aceptada)")
        st.caption("Asigne las fechas de inicio, entrega y límite. La fecha de recepción se calcula automáticamente a 2 días hábiles antes del inicio.")
        
        conn, engine = cdb.get_db_connection()
        c = conn.cursor()
        c.execute("""
            SELECT s.id as sub_id, m.id as master_id, m.no_folio, m.no_solicitud, m.no_cotizacion,
                   m.cliente, m.es_in_situ, s.estado, s.motivo_reprogramacion,
                   m.orden_compra_cliente, m.fecha_aceptacion_cotizacion
            FROM sub_solicitudes_at s
            JOIN solicitudes_master m ON s.solicitud_id = m.id
            WHERE s.clave_area = ? AND s.estado IN ('EN_PROGRAMACION', 'REPROGRAMACION')
            ORDER BY s.id DESC
        """, (at_actual,))
        pendientes_prog = c.fetchall()
        conn.close()
        
        if not pendientes_prog:
            st.success(f"🎉 No hay servicios pendientes de programar fechas para **{at_actual}**.")
        else:
            for sp in pendientes_prog:
                is_rep = (sp['estado'] == 'REPROGRAMACION')
                b_color = "🔴 REPROGRAMACIÓN SOLICITADA POR CLIENTE" if is_rep else "📅 PROGRAMACIÓN PENDIENTE"
                
                with st.expander(f"Folio: {sp['no_folio']} | Cotización: {sp['no_cotizacion']} | {sp['cliente']} [{b_color}]", expanded=True):
                    if sp.get('orden_compra_cliente'):
                        st.info(f"📄 **Orden de Compra / Oficio del Cliente:** `{sp['orden_compra_cliente']}` | **Aceptada:** `{sp.get('fecha_aceptacion_cotizacion') or 'N/A'}`")
                    if is_rep and sp['motivo_reprogramacion']:
                        st.warning(f"⚠️ **Motivo de reprogramación indicado por el cliente:**\n{sp['motivo_reprogramacion']}", icon="⚠️")
                        
                    conn, engine = cdb.get_db_connection()
                    c = conn.cursor()
                    c.execute("SELECT * FROM partidas WHERE sub_solicitud_id = ? AND aceptada_cliente = 1 ORDER BY numero_partida", (sp['sub_id'],))
                    partidas_prog = c.fetchall()
                    conn.close()
                    
                    st.markdown("#### Asignación de Calendario de Laboratorio por Partida")
                    
                    fechas_por_partida = {}
                    for p in partidas_prog:
                        st.markdown(f"**Partida {p['numero_partida']}: {p['descripcion_equipo']}** (Tiempo cal. cotizado: **{p['tiempo_dias_habiles']} días hábiles** | Cantidad: **{p['cantidad']}**)")
                        if p.get('comentarios_cliente'):
                            st.caption(f"📋 *Condiciones acordadas con el cliente:* {p['comentarios_cliente']}")
                        if p.get('comentarios_ssi'):
                            st.caption(f"🔒 *Notas para SSI:* {p['comentarios_ssi']}")
                        col_f1, col_f2, col_f3, col_f4 = st.columns(4)
                        with col_f2:
                            def_ini = date.today() + timedelta(days=14)
                            if p['fecha_inicio_calibracion']:
                                try: def_ini = datetime.strptime(p['fecha_inicio_calibracion'], "%Y-%m-%d").date()
                                except: pass
                            f_ini = st.date_input("Fecha Inicio Calibración *:", value=def_ini, key=f"c_fini_{p['id']}")
                            
                            # Sincronización automática de recepción (-2 días hábiles)
                            prev_ini_k = f"c_prev_fini_{p['id']}"
                            if prev_ini_k in st.session_state and st.session_state[prev_ini_k] != f_ini:
                                f_ini_dt = datetime.combine(f_ini, datetime.min.time())
                                st.session_state[f"c_frec_{p['id']}"] = cdb.restar_dias_habiles(f_ini_dt, 2).date()
                                d_h = int(p['tiempo_dias_habiles'] or 5)
                                st.session_state[f"c_ffin_{p['id']}"] = cdb.sumar_dias_habiles(f_ini_dt, d_h).date()
                            st.session_state[prev_ini_k] = f_ini
                            
                        with col_f1:
                            f_ini_dt = datetime.combine(f_ini, datetime.min.time())
                            f_rec_auto = cdb.restar_dias_habiles(f_ini_dt, 2).date()
                            if p['fecha_recepcion_equipo']:
                                try: f_rec_auto = datetime.strptime(p['fecha_recepcion_equipo'], "%Y-%m-%d").date()
                                except: pass
                            f_rec = st.date_input("Fecha Recepción (-2 días hábiles):", value=f_rec_auto, key=f"c_frec_{p['id']}")
                        with col_f3:
                            dias_h = int(p['tiempo_dias_habiles'] or 5)
                            f_fin_auto = cdb.sumar_dias_habiles(f_ini_dt, dias_h).date()
                            if p['fecha_entrega_equipo']:
                                try: f_fin_auto = datetime.strptime(p['fecha_entrega_equipo'], "%Y-%m-%d").date()
                                except: pass
                            f_fin = st.date_input("Fecha Entrega / Fin *:", value=f_fin_auto, key=f"c_ffin_{p['id']}")
                        with col_f4:
                            f_lim_auto = date.today() + timedelta(days=21)
                            if p['fecha_limite_aceptacion']:
                                try: f_lim_auto = datetime.strptime(p['fecha_limite_aceptacion'], "%Y-%m-%d").date()
                                except: pass
                            f_lim = st.date_input("Fecha Límite Aceptación:", value=f_lim_auto, key=f"c_flim_{p['id']}")
                            
                        fechas_por_partida[p['id']] = {
                            "recepcion": f_rec.strftime("%Y-%m-%d"),
                            "inicio": f_ini.strftime("%Y-%m-%d"),
                            "entrega": f_fin.strftime("%Y-%m-%d"),
                            "limite": f_lim.strftime("%Y-%m-%d")
                        }
                        st.write("")
                        
                    if st.button("🚀 Enviar Fechas Programadas a SSI", key=f"c_btn_send_p_{sp['sub_id']}", type="primary"):
                        conn, engine = cdb.get_db_connection()
                        c = conn.cursor()
                        for pid, f_dict in fechas_por_partida.items():
                            c.execute("""
                            UPDATE partidas
                            SET fecha_recepcion_equipo = ?, fecha_inicio_calibracion = ?,
                                fecha_fin_calibracion = ?, fecha_entrega_equipo = ?, fecha_limite_aceptacion = ?
                            WHERE id = ?
                            """, (f_dict['recepcion'], f_dict['inicio'], f_dict['entrega'], f_dict['entrega'], f_dict['limite'], pid))
                            
                        first_f = list(fechas_por_partida.values())[0] if fechas_por_partida else {}
                        c.execute("""
                        UPDATE sub_solicitudes_at
                        SET estado = 'PROGRAMA_PROPUESTO', motivo_reprogramacion = NULL,
                            fecha_recepcion_prog = ?, fecha_inicio_prog = ?,
                            fecha_entrega_prog = ?, fecha_limite_prog = ?
                        WHERE id = ?
                        """, (
                            first_f.get('recepcion'), first_f.get('inicio'),
                            first_f.get('entrega'), first_f.get('limite'),
                            sp['sub_id']
                        ))
                        c.execute("UPDATE solicitudes_master SET estado = 'PROGRAMA_PROPUESTO' WHERE id = ?", (sp['master_id'],))
                        conn.commit()
                        conn.close()
                        
                        cdb.log_auditoria(user['correo'], "PROGRAMAR_FECHAS", "SUB_SOLICITUD", sp['sub_id'], {"folio": sp['no_folio']})
                        st.session_state["flash_msg"] = ("success", f"🗓️ ¡Fechas programadas para Folio **{sp['no_folio']}** enviadas a SSI con éxito!")
                        st.rerun()

    # AT PESTAÑA 3: CALENDARIO CONFIRMADO
    with at_tab3:
        st.subheader("Servicios Confirmados y Reservas en Laboratorio")
        conn, engine = cdb.get_db_connection()
        c = conn.cursor()
        c.execute("""
            SELECT s.id as sub_id, m.no_folio, m.no_cotizacion, m.cliente,
                   s.fecha_recepcion_prog, s.fecha_inicio_prog, s.fecha_entrega_prog
            FROM sub_solicitudes_at s
            JOIN solicitudes_master m ON s.solicitud_id = m.id
            WHERE s.clave_area = ? AND s.estado = 'PROGRAMA_CONFIRMADO'
            ORDER BY s.fecha_inicio_prog ASC
        """, (at_actual,))
        confirmados = c.fetchall()
        conn.close()
        
        if not confirmados:
            st.info("Aún no hay servicios confirmados en el calendario de este laboratorio.")
        else:
            st.dataframe(pd.DataFrame([{
                "Folio": r['no_folio'],
                "Cotización": r['no_cotizacion'],
                "Cliente": r['cliente'],
                "Fecha Recepción": r['fecha_recepcion_prog'],
                "Fecha Inicio": r['fecha_inicio_prog'],
                "Fecha Entrega": r['fecha_entrega_prog'],
                "Estado": "🔒 RESERVA CONFIRMADA"
            } for r in confirmados]), width="stretch")
