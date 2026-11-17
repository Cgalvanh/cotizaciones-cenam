import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta, date
import database as db
import pdf_generator as pdf_gen
import request_parser as parser

st.set_page_config(
    page_title="Sistema de Cotización y Programación - CENAM",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inicializar Base de Datos una sola vez
@st.cache_resource(show_spinner=False)
def ensure_local_db_ready():
    db.init_db()
    return True

ensure_local_db_ready()

# Carga de alta velocidad y bajo consumo para datos estáticos (Catálogos y Áreas)
@st.cache_data(ttl=3600, show_spinner=False)
def load_cached_catalog_data():
    conn = db.get_connection()
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

# Sidebar Navigation
logo_local = "static/img/logo_cenam.png" if os.path.exists("static/img/logo_cenam.png") else "nube_segura/static/logo_cenam.png"
if os.path.exists(logo_local):
    st.sidebar.image(logo_local, width=190)
else:
    st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/thumb/c/cc/CENAM_logo.svg/320px-CENAM_logo.svg.png", width=180)

st.sidebar.title("Sistema de Servicios CENAM")
rol_seleccionado = st.sidebar.radio("Seleccione Perfil de Operación:", ["🏢 Ventanilla SSI (Coordinador de Servicios)", "🔬 Área Técnica AT (Laboratorios)"])

st.sidebar.markdown("---")
st.sidebar.caption("Procedimiento formal para la recepción, cotización y programación de servicios metrológicos (Contingencia SCS).")

# ==========================================
# ROL 1: VENTANILLA SSI (COORDINADOR DE SERVICIOS - CS)
# ==========================================
if rol_seleccionado == "🏢 Ventanilla SSI (Coordinador de Servicios)":
    st.title("🏢 Ventanilla Central de Servicios (SSI)")
    st.markdown("Gestión integral: recepción de solicitudes, cotizaciones consolidadas, programación de fechas por AT y formalización de contratos.")
    
    # Notificaciones y Contadores en Tiempo Real
    conn = db.get_connection()
    c = conn.cursor()
    
    # 1. Devueltas pendientes de reasignar
    c.execute("SELECT COUNT(*) FROM sub_solicitudes_at WHERE estado = 'DEVUELTA'")
    devueltas_count = c.fetchone()[0] or 0
    
    # 2. Cotizaciones listas para consolidar
    c.execute("""
        SELECT COUNT(DISTINCT m.id)
        FROM solicitudes_master m
        JOIN sub_solicitudes_at s ON m.id = s.solicitud_id
        WHERE m.estado IN ('TURNADA', 'EMITIDA')
        GROUP BY m.id
        HAVING COUNT(s.id) = SUM(CASE WHEN s.estado = 'COMPLETADA' THEN 1 ELSE 0 END)
    """)
    cotiz_listas = len(c.fetchall())
    
    # 3. Solicitudes con cotización enviada esperando aceptación del cliente
    c.execute("SELECT COUNT(*) FROM solicitudes_master WHERE estado = 'COTIZACION_ENVIADA'")
    esperando_acep = c.fetchone()[0] or 0
    
    # 4. Solicitudes con programas propuestos por AT listos para enviar al cliente
    c.execute("""
        SELECT COUNT(DISTINCT s.id)
        FROM sub_solicitudes_at s
        JOIN solicitudes_master m ON s.solicitud_id = m.id
        WHERE s.estado = 'PROGRAMA_PROPUESTO'
    """)
    prog_propuestas = c.fetchone()[0] or 0

    conn.close()
    
    # Alertas visuales
    if devueltas_count > 0:
        st.warning(f"⚠️ **Atención SSI:** Hay **{devueltas_count} solicitud(es) devuelta(s)** por Áreas Técnicas que requieren reasignación inmediata.", icon="⚠️")
    if cotiz_listas > 0:
        st.info(f"🔔 **Aviso SSI:** Hay **{cotiz_listas} cotización(es)** con respuestas completas de Áreas Técnicas listas para emitir y enviar al cliente.", icon="🔔")
    if prog_propuestas > 0:
        st.info(f"📅 **Aviso Programación:** Hay **{prog_propuestas} programa(s) de fechas** propuestos por Laboratorios listos para enviar al cliente.", icon="📅")

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📝 1. Nueva Solicitud",
        f"⚠️ 2. Devueltas ({devueltas_count})",
        f"🏷️ 3. Emisión Cotización ({cotiz_listas})",
        f"📅 4. Aceptación y Programación ({esperando_acep + prog_propuestas})",
        "📜 5. Contratos y Confirmación"
    ])
    
    # TAB 1: NUEVA SOLICITUD
    with tab1:
        st.subheader("Recepción y Registro de Solicitud de Calibración (Formato Solicitud CENAM PR)")
        
        # 1.1 Carga Rápida / Pegar Texto de Correo o Subir Formato DOCX
        with st.expander("📥 Carga Rápida desde Formato Oficial o Correo (Cero Transcripción)", expanded=True):
            st.caption("Obtenga automáticamente todos los datos del cliente y sus instrumentos sin transcribir a mano. Puede subir el archivo `.docx` o `.txt` enviado por el cliente o pegar el cuerpo del correo.")
            col_up1, col_up2 = st.columns([1, 1])
            with col_up1:
                uploaded_doc = st.file_uploader("Opción A: Subir archivo Solicitud CENAM PR (.docx o .txt):", type=["docx", "txt"], key="up_sol_doc")
            with col_up2:
                raw_email_text = st.text_area("Opción B: O pegar texto / cuerpo de correo recibido:", height=95, placeholder="SOLICITUD DE COTIZACIÓN DE SERVICIO DE CALIBRACIÓN...\n1. Datos del solicitante...\n2. Información del instrumento...", key="raw_email_input")
            
            if st.button("✨ Auto-extraer Datos y Llenar Formulario", type="primary", width="stretch"):
                parsed = None
                if uploaded_doc is not None:
                    parsed = parser.parse_solicitud_input(file_source=uploaded_doc)
                elif raw_email_text and raw_email_text.strip():
                    parsed = parser.parse_solicitud_input(raw_text=raw_email_text)
                    
                if parsed and (parsed.get("empresa") or parsed.get("instrumentos") or parsed.get("no_solicitud")):
                    st.session_state["parsed_data"] = parsed
                    st.session_state["form_v"] = st.session_state.get("form_v", 0) + 1
                    inst_count = len(parsed.get("instrumentos", []))
                    st.session_state["flash_msg"] = ("success", f"✨ Datos extraídos exitosamente: Cliente: **{parsed['empresa'] or 'Detectado'}** | **{inst_count} instrumento(s)** clasificados por Área Técnica.")
                    st.rerun()
                else:
                    st.warning("⚠️ No se detectaron datos suficientes en el archivo o texto proporcionado. Verifique que corresponda al formato oficial de Solicitud CENAM PR.")

        parsed_data = st.session_state.get("parsed_data", {})
        form_v = st.session_state.get("form_v", 0)
        
        with st.form("form_nueva_solicitud_pr", clear_on_submit=True):
            st.markdown("#### 1. Datos del Solicitante")
            c1, c2, c3 = st.columns(3)
            with c1:
                cliente_val = parsed_data.get("empresa") or "ECOLOGIA INTEGRADA APLICADA"
                cliente = st.text_input("Razón Social / Nombre del Cliente *", value=cliente_val, key=f"cli_{form_v}")
                rep_val = parsed_data.get("contacto") or "Ing. Alba Vázquez Espinosa"
                representante = st.text_input("Representante / Contacto", value=rep_val, key=f"rep_{form_v}")
            with c2:
                mail_val = parsed_data.get("correo") or "alba_ecol@hotmail.com"
                correo = st.text_input("Correo Electrónico *", value=mail_val, key=f"mail_{form_v}")
                tel_val = parsed_data.get("telefono") or "961 61 591 19"
                telefono = st.text_input("Teléfono", value=tel_val, key=f"tel_{form_v}")
            with c3:
                rfc_val = parsed_data.get("rfc") or "EIA050512XYZ"
                rfc = st.text_input("RFC", value=rfc_val, key=f"rfc_{form_v}")
                pais_val = parsed_data.get("pais") or "México"
                pais = st.text_input("País de Solicitud *", value=pais_val, key=f"pais_{form_v}")
                
            st.markdown("---")
            st.markdown("#### 2. Consecutivos Institucionales y Modalidad del Expediente")
            c_fol1, c_fol2 = st.columns([1.5, 2])
            with c_fol1:
                next_fol = parsed_data.get("no_folio") or db.get_next_folio_number()
                st.info(f"📁 **No. de Folio Asignado:** `{next_fol}`")
            with c_fol2:
                st.caption("ℹ️ **Regla Operativa CENAM (1 Folio ➔ N Solicitudes):** SSI asigna este único Folio maestro para la trazabilidad integral del expediente cliente. El sistema generará una Solicitud independiente con consecutivo PR para cada Área Técnica / División y para los servicios que se realicen IN SITU con viáticos.")
                
            es_extranjero = (pais.strip().lower() != "mexico" and pais.strip().lower() != "méxico")
            if es_extranjero:
                st.warning(f"⚠️ Solicitante en el extranjero detectado ({pais}). En términos de la Ley del IVA, el impuesto no aplica si el servicio es aprovechado en su totalidad en el extranjero.")
                aplica_iva = st.checkbox("¿Exentar IVA (0%) para este cliente extranjero?", value=True, key=f"iva_{form_v}")
            else:
                aplica_iva = st.checkbox("Aplica IVA general del 16%", value=True, key=f"iva_{form_v}")
                
            st.markdown("---")
            st.markdown("#### 3. Instrumentos a Calibrar y Clasificación por División / Modalidad")
            st.caption("Si la solicitud incluye equipos de distintas áreas o servicios en sitio, el sistema los segregará automáticamente bajo el mismo Folio.")
            
            parsed_inst = parsed_data.get("instrumentos", [])
            num_default = len(parsed_inst) if parsed_inst else 2
            num_equipos = st.number_input("Número de instrumentos en la solicitud", min_value=1, max_value=30, value=num_default, key=f"num_eq_{form_v}")
            
            equipos_data = []
            for i in range(int(num_equipos)):
                p_item = parsed_inst[i] if i < len(parsed_inst) else {}
                st.markdown(f"**Instrumento {i+1}**")
                
                col_i1, col_i2, col_i3, col_i4 = st.columns([3, 2, 2, 1.2])
                with col_i1:
                    d_val = p_item.get("descripcion") or ("Detector de fugas acústico" if i==0 else "Multímetro digital 6.5 dígitos")
                    desc_eq = st.text_input(f"Descripción del Instrumento {i+1} *", key=f"desc_{i}_{form_v}", value=d_val)
                    alc_val = p_item.get("intervalo") or ("<= 80 kHz" if i==0 else "100 mV a 1000 V")
                    alcance_eq = st.text_input(f"Intervalo / Puntos requeridos {i+1}", key=f"alc_{i}_{form_v}", value=alc_val)
                    cert_val = p_item.get("certificado_anterior") or ""
                    cert_eq = st.text_input(f"Certificado anterior o No. equipo CENAM {i+1}", key=f"cert_{i}_{form_v}", value=cert_val)
                with col_i2:
                    m_val = p_item.get("marca") or ("Mesa Engineering" if i==0 else "Fluke")
                    marca_eq = st.text_input(f"Marca {i+1}", key=f"marca_{i}_{form_v}", value=m_val)
                    mod_val = p_item.get("modelo") or ("2D" if i==0 else "8846A")
                    modelo_eq = st.text_input(f"Modelo {i+1}", key=f"mod_{i}_{form_v}", value=mod_val)
                    mag_val = p_item.get("magnitud") or ("Vibraciones y Acústica" if i==0 else "Eléctrica")
                    magnitud_eq = st.text_input(f"Magnitud {i+1}", key=f"mag_{i}_{form_v}", value=mag_val)
                with col_i3:
                    ser_val = p_item.get("serie") or f"SN-{1000+i}"
                    serie_eq = st.text_input(f"No. de Serie {i+1}", key=f"ser_{i}_{form_v}", value=ser_val)
                    id_val = p_item.get("id_interno") or f"PR-EQ-{i+1:02d}"
                    id_int_eq = st.text_input(f"Identificación Interna {i+1}", key=f"idint_{i}_{form_v}", value=id_val)
                    sug_at = p_item.get("clave_area_sugerida") or parser.sugerir_area_por_magnitud_y_texto(magnitud_eq, desc_eq)
                    mapping_old_at = {'AT-01': '740', 'AT-02': '410', 'AT-03': '440', 'AT-04': '430', 'AT-05': '420', 'AT-06': '520', 'AT-07': '730', 'AT-08': '720', 'AT-09': '710', 'AT-10': '510', 'AT-11': '700', 'AT-12': '630', 'AT-13': '620', 'AT-14': '810'}
                    sug_at = mapping_old_at.get(sug_at, sug_at)
                    at_dest = st.selectbox(
                        f"División Destino {i+1}",
                        options=list(areas_dict.keys()),
                        format_func=lambda x: f"{x} - {areas_dict[x]} [{areas_dir_dict.get(x, '')}]" if areas_dir_dict.get(x) else f"{x} - {areas_dict[x]}",
                        index=list(areas_dict.keys()).index(sug_at) if sug_at in areas_dict else 0,
                        key=f"at_{i}_{form_v}"
                    )
                with col_i4:
                    it_insitu = st.checkbox(f"🚗 IN SITU {i+1}", value=False, key=f"insitu_{i}_{form_v}", help="Marque si este servicio se realizará en planta del cliente con viáticos.")
                
                cond_val = p_item.get("condiciones") or ""
                cond_eq = st.text_input(f"Condiciones particulares de calibración {i+1} (Opcional)", key=f"cond_{i}_{form_v}", value=cond_val)
                
                equipos_data.append({
                    "numero": i+1,
                    "desc": desc_eq,
                    "marca": marca_eq,
                    "modelo": modelo_eq,
                    "serie": serie_eq,
                    "magnitud": magnitud_eq,
                    "alcance": alcance_eq,
                    "certificado_anterior": cert_eq,
                    "id_interno": id_int_eq,
                    "condiciones": cond_eq,
                    "clave_area": at_dest,
                    "es_in_situ": 1 if it_insitu else 0
                })
                st.divider()
                
            from collections import defaultdict
            pre_grupos = defaultdict(int)
            for it in equipos_data:
                mod_name = "🚗 IN SITU (Viáticos)" if it['es_in_situ'] else "🔬 LAB CENAM"
                pre_grupos[(it['clave_area'], mod_name)] += 1
                
            st.markdown("##### 🔍 Previsualización de Solicitudes a Generar:")
            c_prev_cols = st.columns(len(pre_grupos) or 1)
            for idx_g, ((g_area, g_mod), g_count) in enumerate(pre_grupos.items()):
                with c_prev_cols[idx_g % len(c_prev_cols)]:
                    st.success(f"**División {g_area}**\n\n{areas_dict.get(g_area, '')}\n\n`{g_mod}`: **{g_count} partida(s)**")
                    
            btn_guardar = st.form_submit_button("🚀 Registrar Expediente y Turnar Solicitudes a ATs", type="primary")
            
            if btn_guardar:
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
                
                res = db.crear_expediente_y_solicitudes(cliente_dict, equipos_data, "ssi@cenam.mx")
                
                if "parsed_data" in st.session_state:
                    del st.session_state["parsed_data"]
                    
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
    with tab2:
        st.subheader("Bandeja de Solicitudes Devueltas por Áreas Técnicas (No Corresponde)")
        conn = db.get_connection()
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
                        nueva_area = st.selectbox(
                            "Reasignar a nueva Área Técnica:",
                            options=list(areas_dict.keys()),
                            format_func=lambda x: f"{x} - {areas_dict[x]} [{areas_dir_dict.get(x, '')}]" if areas_dir_dict.get(x) else f"{x} - {areas_dict[x]}",
                            index=sug_idx,
                            key=f"reasig_{d['sub_id']}"
                        )
                        if st.button("🔄 Confirmar Reasignación", key=f"btn_reasig_{d['sub_id']}"):
                            conn = db.get_connection()
                            c = conn.cursor()
                            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            c.execute("""
                            UPDATE sub_solicitudes_at
                            SET clave_area = ?, estado = 'ASIGNADA', motivo_devolucion = NULL,
                                area_sugerida = NULL, fecha_asignacion = ?, fecha_limite_sla = ?
                            WHERE id = ?
                            """, (nueva_area, now_str, (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d"), d['sub_id']))
                            conn.commit()
                            conn.close()
                            
                            st.session_state["flash_msg"] = (
                                "success",
                                f"🔄 Solicitud **{d['no_folio']}** reasignada exitosamente a **{nueva_area} - {areas_dict.get(nueva_area, '')}**. Desaparece de esta bandeja y el nuevo AT ha sido notificado."
                            )
                            st.toast(f"Folio {d['no_folio']} reasignado a {nueva_area}", icon="🔄")
                            st.rerun()

    # TAB 3: EMISIÓN Y ENVÍO DE COTIZACIÓN
    with tab3:
        st.subheader("Consolidación y Emisión de Cotización Oficial / DSNR hacia el Cliente")
        st.caption("Solo se muestran cotizaciones en elaboración. Al enviar la cotización al cliente, pasa a la siguiente fase de Aceptación y Programación.")
        
        modo_vista_tab3 = st.radio("Modo de Consulta:", ["📋 Consolidación por Solicitud", "📁 Vista Integral de Expedientes (1 Folio ➔ N Solicitudes)"], horizontal=True, key="modo_tab3_local")
        
        if modo_vista_tab3 == "📁 Vista Integral de Expedientes (1 Folio ➔ N Solicitudes)":
            expedientes_all = db.get_expedientes_resumen()
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
            solicitudes = c.fetchall()
            
            # OPTIMIZACIÓN BD: Consulta por lotes (Batch Query) de todas las partidas
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
                estado_tag = "✅ LISTA PARA CONSOLIDAR Y ENVIAR" if is_ready else f"⏳ EN PROCESO ({s['subs_completadas']}/{s['total_subs']} áreas terminadas)"
                
                with st.expander(f"Folio: {s['no_folio']} | Solicitud: {s['no_solicitud']} | {s['cliente']} [{estado_tag}]", expanded=is_ready):
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
                                        conn_fix = db.get_connection()
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
                            "Partida": p['numero_partida'],
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
                            "Estado": "🔴 DSNR (No Realizable)" if p['es_no_realizable'] == 1 else "🟢 Realizable"
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
                                            key=f"fix_ssel_{cp['id']}"
                                        )
                                        if st.button("💾 Guardar y Asignar Precio a esta Partida", key=f"btn_fix_{cp['id']}"):
                                            s_chosen = serv_by_clave[s_fix_sel]
                                            p_unit_fix = float(s_chosen['costo'])
                                            cant_fix = int(cp.get('cantidad') or 1)
                                            tot_fix = p_unit_fix * cant_fix
                                            conn = db.get_connection()
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
                                            st.session_state["flash_msg"] = ("success", f"✅ Partida {cp['numero_partida']} corregida con precio ${p_unit_fix:,.2f}.")
                                            st.rerun()
                        with c_fix_col2:
                            with st.popover("↩️ Devolver Solicitud a CS-AT"):
                                st.markdown("**Devolución para Re-cotización:**")
                                mot_dev_ui = st.text_area(
                                    "Motivo de devolución a las Áreas Técnicas:",
                                    value="Favor de registrar los costos unitarios del catálogo oficial (la solicitud presenta partidas con costo $0.00).",
                                    key=f"mot_dev_ceros_{s['id']}"
                                )
                                if st.button("Confirmar Devolución al Especialista", key=f"btn_dev_ceros_{s['id']}", type="primary"):
                                    conn = db.get_connection()
                                    c = conn.cursor()
                                    c.execute("UPDATE sub_solicitudes_at SET estado = 'DEVUELTA', motivo_devolucion = ? WHERE solicitud_id = ?", (mot_dev_ui, s['id']))
                                    c.execute("UPDATE solicitudes_master SET estado = 'DEVUELTA' WHERE id = ?", (s['id'],))
                                    conn.commit()
                                    conn.close()
                                    st.session_state["flash_msg"] = ("warning", f"↩️ Solicitud **{s['no_solicitud']}** devuelta a CS-AT para corrección de costos.")
                                    st.rerun()
                    
                    col_c1, col_c2, col_c3 = st.columns([2, 2, 3])
                    with col_c1:
                        if not s['no_cotizacion'] and is_ready:
                            if hay_ceros:
                                st.button("🏷️ Asignar No. Cotización (Bloqueado por Precios $0.00)", disabled=True, key=f"dis_cot_{s['id']}")
                            else:
                                next_cotiz = db.get_next_cotizacion_number()
                                if st.button(f"🏷️ Asignar No. Cotización ({next_cotiz})", key=f"btn_cot_{s['id']}"):
                                    conn = db.get_connection()
                                    c = conn.cursor()
                                    c.execute("""
                                    UPDATE solicitudes_master
                                    SET no_cotizacion = ?, estado = 'EMITIDA', fecha_emision = ?
                                    WHERE id = ?
                                    """, (next_cotiz, datetime.now().strftime("%Y-%m-%d"), s['id']))
                                    conn.commit()
                                    conn.close()
                                    st.session_state["flash_msg"] = ("success", f"🏷️ No. de Cotización **{next_cotiz}** asignado con éxito. Ya puede descargar los PDFs y enviarlos al cliente.")
                                    st.rerun()
                        elif s['no_cotizacion']:
                            st.success(f"No. Cotización: **{s['no_cotizacion']}**")
                            
                    with col_c2:
                        os.makedirs("generated_docs", exist_ok=True)
                        if has_viable and s['no_cotizacion'] and not hay_ceros:
                            pdf_path = f"generated_docs/Cotizacion_{s['no_folio'].replace('-', '_')}_{s['no_cotizacion']}.pdf"
                            sol_dict = dict(s)
                            parts_list = [dict(p) for p in parts]
                            pdf_gen.generate_cotizacion_pdf(sol_dict, parts_list, pdf_path)
                            with open(pdf_path, "rb") as f:
                                st.download_button(
                                    "📥 Descargar Cotización Oficial PDF",
                                    data=f,
                                    file_name=f"Cotizacion_{s['no_folio']}.pdf",
                                    mime="application/pdf",
                                    key=f"dl_cot_{s['id']}"
                                )
                        if has_dsnr:
                            pdf_dsnr_path = f"generated_docs/DSNR_{s['no_folio'].replace('-', '_')}.pdf"
                            sol_dict = dict(s)
                            dsnr_parts = [dict(p) for p in parts if p['es_no_realizable'] == 1]
                            pdf_gen.generate_dsnr_pdf(sol_dict, dsnr_parts, "Dirección de Metrología", pdf_dsnr_path)
                            with open(pdf_dsnr_path, "rb") as f:
                                st.download_button(
                                    "📄 Descargar DSNR PR PDF",
                                    data=f,
                                    file_name=f"DSNR_PR_{s['no_folio']}.pdf",
                                    mime="application/pdf",
                                    key=f"dl_dsnr_{s['id']}"
                                )
                                
                    with col_c3:
                        if (s['no_cotizacion'] and not hay_ceros) or (not has_viable and has_dsnr):
                            with st.popover("✉️ Enviar Cotización al Cliente"):
                                st.markdown(f"**Destinatario:** `{s['correo']}`")
                                asunto_mail = f"CENAM - Cotizacion Oficial Folio {s['no_folio']} / Solicitud {s['no_solicitud']}"
                                cuerpo_mail = f"Estimado(a) {s['representante'] or s['cliente']}:%0D%0A%0D%0APor medio de la presente, el Centro Nacional de Metrologia (CENAM) hace entrega formal de la Cotizacion No. {s['no_cotizacion'] or ''} correspondiente a su solicitud con Folio {s['no_folio']}.%0D%0A%0D%0AFavor de revisar el documento PDF adjunto y regresar el formato con las partidas aceptadas marcadas.%0D%0A%0D%0AAtentamente,%0D%0AVentanilla Central de Servicios (SSI)%0D%0ACENAM"
                                mailto_url = f"mailto:{s['correo']}?subject={asunto_mail}&body={cuerpo_mail}"
                                st.markdown(f"[📬 Abrir Correo Institucional]({mailto_url})")
                                st.caption("Haga clic arriba para abrir su cliente de correo y adjunte el PDF descargado.")
                                st.write("")
                                if st.button("🚀 Confirmar Envío al Cliente y Pasar a Programación", key=f"btn_send_cot_{s['id']}", type="primary"):
                                    conn = db.get_connection()
                                    c = conn.cursor()
                                    c.execute("UPDATE solicitudes_master SET estado = 'COTIZACION_ENVIADA' WHERE id = ?", (s['id'],))
                                    conn.commit()
                                    conn.close()
                                    st.session_state["flash_msg"] = (
                                        "success",
                                        f"✅ La Cotización del Folio **{s['no_folio']}** ha sido enviada al cliente. Pasa a la pestaña '4. Aceptación y Programación' para esperar la respuesta del cliente."
                                    )
                                    st.toast(f"Folio {s['no_folio']} enviado a cliente", icon="📤")
                                    st.rerun()

    # TAB 4: ACEPTACIÓN DEL CLIENTE Y PROGRAMACIÓN POR ÁREA TÉCNICA
    with tab4:
        st.subheader("Gestión de Aceptación y Programación de Fechas por Área Técnica (CS-AT)")
        st.caption("Una vez aceptada la cotización por el cliente, las partidas aprobadas se turnan a cada Área Técnica para asignar calendario de laboratorio.")
        
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
        sol_prog = c.fetchall()
        
        # OPTIMIZACIÓN BD: Batch queries para Tab 4
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
                    
                    # 4.1 FASE A: CLIENTE ACEPTA COTIZACIÓN
                    if s['estado'] == 'COTIZACION_ENVIADA':
                        st.markdown("#### Aceptación de Partidas por el Cliente")
                        col_oc1, col_oc2 = st.columns(2)
                        with col_oc1:
                            oc_val = st.text_input("📄 No. de Orden de Compra u Oficio de Aceptación:", value=s.get('orden_compra_cliente') or "", key=f"oc_{s['id']}", placeholder="Ej. OC-2026-0812 / OF-CLI-554")
                        with col_oc2:
                            f_acep = st.date_input("📅 Fecha de Aceptación por el Cliente:", value=date.today(), key=f"f_acep_{s['id']}")
                            
                        # Datos desde memoria (Batch Query)
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
                                is_chk = st.checkbox(label_chk, value=True, key=f"chk_acep_{p['id']}")
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
                        
                        if st.button("🚀 Confirmar Aceptación y Turnar a Programación con CS-AT", key=f"btn_turn_prog_{s['id']}", type="primary"):
                            if n_acep == 0:
                                st.error("Debe seleccionar al menos una partida aceptada para turnar a programación.")
                            else:
                                conn = db.get_connection()
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
                                
                                st.session_state["flash_msg"] = (
                                    "success",
                                    f"📅 Cotización Folio **{s['no_folio']}** aceptada ({n_acep} partidas aceptadas). Se turnó a programación con CS-AT."
                                )
                                st.toast(f"Folio {s['no_folio']} en programación", icon="📅")
                                st.rerun()

                    # 4.2 FASE B: MONITOREO Y ENVÍO DE PROGRAMAS POR ÁREA TÉCNICA (AT)
                    else:
                        st.markdown("#### Propuesta de Programación de Fechas (Emitida por Área Técnica)")
                        st.caption("Conforme a la regla institucional, cada Área Técnica programa sus fechas y se emite un formato de programación separado por AT.")
                        
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
                                    "Entrega Equipo / Fin": p['fecha_entrega_equipo'] or sub['fecha_entrega_prog'] or 'Pendiente AT',
                                    "Límite Aceptación": p['fecha_limite_aceptacion'] or sub['fecha_limite_prog'] or '3 semanas'
                                } for p in sub_parts])
                                st.dataframe(p_df, width="stretch")
                                
                                # Si ya está propuesto el programa por el AT
                                if sub['estado'] in ('PROGRAMA_PROPUESTO', 'PROGRAMA_CONFIRMADO'):
                                    col_p1, col_p2, col_p3 = st.columns([2, 2, 3])
                                    with col_p1:
                                        # Descargar PDF de Programación por AT
                                        os.makedirs("generated_docs", exist_ok=True)
                                        prog_pdf_path = f"generated_docs/Programacion_{s['no_folio'].replace('-', '_')}_{sub['clave_area']}.pdf"
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
                                                key=f"dl_prog_{sub['id']}"
                                            )
                                    with col_p2:
                                        with st.popover("✉️ Enviar Propuesta de Fechas"):
                                            st.markdown(f"**Destinatario:** `{s['correo']}`")
                                            asunto_p = f"CENAM - Propuesta de Programacion {sub['clave_area']} Folio {s['no_folio']}"
                                            body_p = f"Estimado(a) {s['representante'] or s['cliente']}:%0D%0A%0D%0ALe informamos las fechas programadas para los servicios de calibracion del Area Tecnica {sub['clave_area']}.%0D%0A%0D%0AFavor de revisar el documento de Programacion adjunto para su aceptacion.%0D%0A%0D%0AAtentamente,%0D%0ACoordinador de Servicios (SSI) - CENAM"
                                            mailto_prog = f"mailto:{s['correo']}?subject={asunto_p}&body={body_p}"
                                            st.markdown(f"[📬 Abrir Correo con Propuesta]({mailto_prog})")
                                            if st.button("Confirmar Envío al Cliente", key=f"btn_send_p_{sub['id']}"):
                                                st.toast(f"Propuesta enviada al cliente", icon="✉️")
                                    with col_p3:
                                        with st.popover("🔄 Cliente Solicita Cambio de Fecha (Reprogramación)"):
                                            st.markdown("**Solicitud de Reprogramación hacia CS-AT**")
                                            motivo_rep = st.text_area("Indique fechas solicitadas por el cliente o motivo:", key=f"mot_rep_{sub['id']}")
                                            if st.button("Turnar a CS-AT para Modificación", key=f"btn_turn_rep_{sub['id']}"):
                                                conn = db.get_connection()
                                                c = conn.cursor()
                                                c.execute("""
                                                UPDATE sub_solicitudes_at
                                                SET estado = 'REPROGRAMACION', motivo_reprogramacion = ?
                                                WHERE id = ?
                                                """, (motivo_rep, sub['id']))
                                                c.execute("UPDATE solicitudes_master SET estado = 'REPROGRAMACION' WHERE id = ?", (s['id'],))
                                                conn.commit()
                                                conn.close()
                                                st.session_state["flash_msg"] = ("warning", f"🔄 Sub-solicitud turnada de regreso al CS-AT de {sub['clave_area']} para reprogramación de fechas.")
                                                st.rerun()
                            st.write("")
                            
                        # Botón para pasar a la fase final de confirmación si todas las ATs tienen programa propuesto
                        todos_listos = all(sub['estado'] in ('PROGRAMA_PROPUESTO', 'PROGRAMA_CONFIRMADO') for sub in subs_prog)
                        if todos_listos:
                            if st.button("🎉 Cliente Aceptó Programación -> Pasar a Formalizar Contratos", key=f"btn_goto_confirm_{s['id']}", type="primary"):
                                conn = db.get_connection()
                                c = conn.cursor()
                                c.execute("UPDATE solicitudes_master SET estado = 'PROGRAMA_CONFIRMADO' WHERE id = ?", (s['id'],))
                                conn.commit()
                                conn.close()
                                st.session_state["flash_msg"] = ("success", f"📜 Folio {s['no_folio']} listo para formalizar contrato, definir retorno de equipo y confirmar reserva.")
                                st.rerun()

    # TAB 5: CONFIRMACIÓN DEL SERVICIO Y CONTRATOS
    with tab5:
        st.subheader("Formalización de Contratos, Retorno de Equipos y Confirmación Definitiva")
        st.caption("Fase final del procedimiento: emisión de contratos legales de prestación de servicios y notificación de reserva a laboratorios.")
        
        conn = db.get_connection()
        c = conn.cursor()
        c.execute("""
            SELECT * FROM solicitudes_master
            WHERE estado IN ('PROGRAMA_CONFIRMADO', 'CONFIRMADA_CONCLUIDA')
            ORDER BY id DESC
        """)
        sol_conf = c.fetchall()
        
        # OPTIMIZACIÓN BD: Batch queries para Tab 5
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
                        
                        # Retorno de equipos
                        ret_actual = s['modalidad_retorno'] or 'RECOLECCION_CENAM'
                        opciones_ret = {
                            'RECOLECCION_CENAM': 'Opción 1: Mi empresa recogerá el equipo en instalaciones del CENAM',
                            'MENSAJERIA_CLIENTE': 'Opción 2: Mi empresa contratará servicio de mensajería para recolección',
                            'GUIA_PREPAGADA': 'Opción 3: Mi empresa enviará una guía prepagada para el retorno'
                        }
                        nueva_ret = st.radio(
                            "Modalidad de Retorno de Equipo acordada:",
                            options=list(opciones_ret.keys()),
                            format_func=lambda x: opciones_ret[x],
                            index=list(opciones_ret.keys()).index(ret_actual),
                            key=f"ret_{s['id']}"
                        )
                        
                        # Representante legal CENAM (libre a edición o vacío)
                        rep_cenam_actual = s['representante_legal_cenam'] or ""
                        rep_cenam_input = st.text_input(
                            "Representante Legal del CENAM (Dejar vacío para firma autógrafa física):",
                            value=rep_cenam_actual,
                            placeholder="Ej. Lic. Nombre del Representante Legal (o dejar en blanco)",
                            key=f"rep_c_{s['id']}"
                        )
                        
                        if s['es_in_situ']:
                            dir_planta = st.text_input("Dirección de la planta donde se realizará el servicio:", value=s['direccion_servicio_sitio'] or "", key=f"dir_p_{s['id']}")
                            cond_planta = st.text_input("Condiciones de acceso a planta (EPP, inducción):", value=s['condiciones_acceso_planta'] or "Equipo de protección personal completo", key=f"cond_p_{s['id']}")
                        else:
                            dir_planta = None
                            cond_planta = None
                            
                    with c_conf2:
                        st.markdown("#### Descarga de Contratos y Programaciones por AT")
                        
                        subs = subs_by_conf.get(s['id'], [])
                        
                        for sub in subs:
                            parts = parts_by_sub_conf.get(sub['id'], [])
                            
                            if parts:
                                os.makedirs("generated_docs", exist_ok=True)
                                pdf_path = f"generated_docs/Contrato_Programacion_{s['no_folio'].replace('-', '_')}_{sub['clave_area']}.pdf"
                                sol_d = dict(s)
                                sol_d['modalidad_retorno'] = nueva_ret
                                sol_d['direccion_servicio_sitio'] = dir_planta
                                sol_d['condiciones_acceso_planta'] = cond_planta
                                
                                pdf_gen.generate_programacion_pdf(
                                    sol_d, dict(sub), [dict(p) for p in parts],
                                    tipo='IN_SITU' if s['es_in_situ'] else 'CENAM',
                                    filepath=pdf_path,
                                    rep_legal_cenam=rep_cenam_input
                                )
                            
                            if parts:
                                os.makedirs("generated_docs", exist_ok=True)
                                pdf_path = f"generated_docs/Contrato_Programacion_{s['no_folio'].replace('-', '_')}_{sub['clave_area']}.pdf"
                                sol_d = dict(s)
                                sol_d['modalidad_retorno'] = nueva_ret
                                sol_d['direccion_servicio_sitio'] = dir_planta
                                sol_d['condiciones_acceso_planta'] = cond_planta
                                
                                pdf_gen.generate_programacion_pdf(
                                    sol_d, dict(sub), [dict(p) for p in parts],
                                    tipo='IN_SITU' if s['es_in_situ'] else 'CENAM',
                                    filepath=pdf_path,
                                    rep_legal_cenam=rep_cenam_input
                                )
                                
                                with open(pdf_path, "rb") as f:
                                    st.download_button(
                                        f"📜 Descargar Contrato y Programación Oficial ({sub['clave_area']})",
                                        data=f,
                                        file_name=f"Contrato_Programacion_{s['no_folio']}_{sub['clave_area']}.pdf",
                                        mime="application/pdf",
                                        key=f"dl_contrato_{sub['id']}"
                                    )
                                    
                    st.divider()
                    
                    # Confirmación final y bloqueo de laboratorios
                    if not is_concluida:
                        if st.button("🏁 Confirmar Servicio, Reservar Laboratorios y Archivar Trámite", key=f"btn_finish_all_{s['id']}", type="primary"):
                            conn = db.get_connection()
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
                            
                            st.session_state["flash_msg"] = (
                                "success",
                                f"🏁 ¡Servicio confirmado exitosamente! Folio **{s['no_folio']}**. Se ha notificado a los laboratorios CS-AT para la reserva y resguardo de las fechas acordadas."
                            )
                            st.toast(f"Folio {s['no_folio']} confirmado y archivado", icon="🏁")
                            st.rerun()

        st.markdown("---")
        with st.expander("⚙️ Zona de Mantenimiento Local (Reiniciar Solicitudes a Cero)", expanded=False):
            st.warning("Esta opción elimina las solicitudes y programaciones registradas en la base local SQLite, reiniciando los folios a 0001-2026PR.\n\n"
                       "✅ **Catálogos Protegidos:** Catálogo de servicios, laboratorios y áreas técnicas se conservan intactos.")
            with st.popover("🚨 Confirmar Limpieza de Solicitudes Locales"):
                st.error("¿Confirma la depuración de solicitudes y partidas de prueba locales?")
                if st.button("Confirmar y Limpiar Local", type="primary", key="btn_purge_local_db"):
                    eliminados = db.limpiar_solicitudes_y_programaciones()
                    st.session_state["flash_msg"] = ("success", f"🧹 Base de datos local depurada con éxito. Registros eliminados: {eliminados}")
                    st.rerun()

# ==========================================
# ROL 2: ÁREA TÉCNICA (COORDINADOR DE SERVICIOS - CS-AT)
# ==========================================
else:
    st.title("🔬 Área Técnica (AT) - Evaluación, Cotización y Programación de Laboratorio")
    
    col_sel_at, col_sla = st.columns([3, 2])
    with col_sel_at:
        at_actual = st.selectbox(
            "Seleccione su Área Técnica (AT):",
            options=list(areas_dict.keys()),
            format_func=lambda x: f"{x} - {areas_dict[x]} [{areas_dir_dict.get(x, '')}]" if areas_dir_dict.get(x) else f"{x} - {areas_dict[x]}"
        )
    with col_sla:
        st.info("⏱️ **Reglas de Calidad:** 3 días hábiles para cotizar. Para programación, la fecha de recepción será automáticamente 2 días hábiles antes de la fecha de inicio.")
        
    st.markdown("---")
    
    # Pestañas de CS-AT
    at_tab1, at_tab2, at_tab3 = st.tabs(["🔬 1. Cotización Metrológica", "🗓️ 2. Programación de Fechas", "📌 3. Calendario Confirmado"])
    
    # ----------------------------------------------------
    # AT PESTAÑA 1: COTIZACIÓN METROLÓGICA (ETAPA 2)
    # ----------------------------------------------------
    with at_tab1:
        conn = db.get_connection()
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
            st.info(f"🔔 **Aviso CS-AT ({at_actual}):** Tiene **{len(solicitudes_at)} solicitud(es) pendiente(s)** de cotización turnada(s) por SSI.", icon="🔔")
        
        if not solicitudes_at:
            st.success(f"🎉 No hay cotizaciones pendientes para **{at_actual} - {areas_dict[at_actual]}**. ¡Bandeja al día!")
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
                            motivo_dev = st.text_area("Motivo técnico por el cual no corresponde a esta área:", key=f"mot_{sol['sub_id']}")
                            sug_otra = st.selectbox(
                                "Área sugerida que sí debe atenderlo (Opcional):",
                                options=[a for a in areas_dict.keys() if a != at_actual],
                                format_func=lambda x: f"{x} - {areas_dict[x]} [{areas_dir_dict.get(x, '')}]" if areas_dir_dict.get(x) else f"{x} - {areas_dict[x]}",
                                key=f"sug_{sol['sub_id']}"
                            )
                            if st.button("Confirmar Devolución a SSI", key=f"btn_dev_{sol['sub_id']}"):
                                conn = db.get_connection()
                                c = conn.cursor()
                                c.execute("""
                                UPDATE sub_solicitudes_at
                                SET estado = 'DEVUELTA', motivo_devolucion = ?, area_sugerida = ?
                                WHERE id = ?
                                """, (motivo_dev, sug_otra, sol['sub_id']))
                                conn.commit()
                                conn.close()
                                
                                st.session_state["flash_msg"] = (
                                    "warning",
                                    f"↩️ La solicitud Folio **{sol['no_folio']}** ha sido devuelta a SSI para reasignación y removida de su pantalla. SSI ha sido notificado."
                                )
                                st.toast(f"Folio {sol['no_folio']} devuelto a SSI", icon="↩️")
                                st.rerun()
                                
                    with c_act2:
                        with st.popover("👨‍🔬 Consultar con Especialista de Laboratorio"):
                            st.markdown("**Consulta Técnica Interna por Correo**")
                            nombre_esp = st.text_input("Nombre / Correo del Especialista:", key=f"esp_name_{sol['sub_id']}")
                            duda_tecnica = st.text_area("Pregunta / Duda Técnica:", key=f"esp_preg_{sol['sub_id']}")
                            
                            body_mail = f"Estimado(a) colega:%0D%0A%0D%0ASe recibio la solicitud Folio {sol['no_folio']} para el cliente {sol['cliente']}.%0D%0APregunta: {duda_tecnica}%0D%0A%0D%0AFavor de responder viabilidad metrologica y clave de catalogo aplicable."
                            mailto_url = f"mailto:{nombre_esp}?subject=Consulta%20Tecnica%20Folio%20{sol['no_folio']}&body={body_mail}"
                            st.markdown(f"[✉️ Abrir en Outlook / Correo]({mailto_url})")
                            
                            rpta_esp = st.text_area("Registrar Respuesta del Especialista (Evidencia ISO 17025):", key=f"esp_resp_{sol['sub_id']}")
                            if st.button("Guardar Consulta y Evidencia Técnica", key=f"btn_save_esp_{sol['sub_id']}"):
                                conn = db.get_connection()
                                c = conn.cursor()
                                c.execute("""
                                INSERT INTO consultas_especialistas (
                                    sub_solicitud_id, especialista_nombre, pregunta, respuesta,
                                    fecha_consulta, fecha_respuesta, estado
                                ) VALUES (?, ?, ?, ?, ?, ?, 'CONTESTADA')
                                """, (
                                    sol['sub_id'], nombre_esp, duda_tecnica, rpta_esp,
                                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                    datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                ))
                                c.execute("UPDATE sub_solicitudes_at SET estado = 'EN_CONSULTA' WHERE id = ?", (sol['sub_id'],))
                                conn.commit()
                                conn.close()
                                st.success("Consulta archivada como evidencia técnica.")
                                st.rerun()

                    with c_act3:
                        if not sol['es_in_situ']:
                            with st.popover("🚗 Separar Partidas a Solicitud IN SITU"):
                                st.markdown("##### Segregar Partidas a Modalidad IN SITU")
                                st.caption("Seleccione las partidas que deban realizarse en planta del cliente con viáticos. Se generará una nueva Solicitud bajo el mismo Folio.")
                                
                                conn_temp = db.get_connection()
                                c_temp = conn_temp.cursor()
                                c_temp.execute("SELECT id, numero_partida, descripcion_equipo FROM partidas WHERE sub_solicitud_id = ? ORDER BY numero_partida", (sol['sub_id'],))
                                parts_temp = c_temp.fetchall()
                                conn_temp.close()
                                
                                sel_to_sep = []
                                for pt in parts_temp:
                                    chk_s = st.checkbox(f"Partida {pt['numero_partida']}: {pt['descripcion_equipo']}", key=f"loc_chk_sep_{pt['id']}")
                                    if chk_s:
                                        sel_to_sep.append(pt['id'])
                                        
                                if st.button("🚀 Confirmar Separación IN SITU", key=f"loc_btn_sep_{sol['sub_id']}", type="primary"):
                                    if not sel_to_sep:
                                        st.warning("Seleccione al menos una partida para separar.")
                                    else:
                                        res_sep = db.separar_partidas_in_situ(sol['master_id'], sel_to_sep, "csat@cenam.mx")
                                        st.session_state["flash_msg"] = ("success", f"🚗 Se ha generado la nueva Solicitud IN SITU **{res_sep['nuevo_no_solicitud']}** bajo el Folio **{res_sep['no_folio']}**.")
                                        st.toast(f"Solicitud {res_sep['nuevo_no_solicitud']} creada", icon="🚗")
                                        st.rerun()
                        else:
                            st.info("🚗 Modalidad **IN SITU** (con viáticos)")

                    st.markdown("---")
                    st.markdown("### Partidas Asignadas para Cotización")
                    
                    conn = db.get_connection()
                    c = conn.cursor()
                    c.execute("SELECT * FROM partidas WHERE sub_solicitud_id = ? ORDER BY numero_partida", (sol['sub_id'],))
                    partidas_at = c.fetchall()
                    conn.close()
                    
                    # Catálogo en RAM (0 consultas de red a BD)
                    servicios_area = serv_by_area.get(str(at_actual), [])
                    labs_disponibles = sorted(list(set(s['codigo_laboratorio'] for s in servicios_area if s.get('codigo_laboratorio'))))
                    
                    for p in partidas_at:
                        st.markdown(f"**Partida {p['numero_partida']}: {p['descripcion_equipo']}**")
                        st.caption(f"Marca: `{p['marca']}` | Modelo: `{p['modelo']}` | Serie: `{p['no_serie']}` | ID Interno: `{p['id_interno']}` | Cert. anterior: `{p['certificado_anterior'] or 'N/A'}`")
                        
                        col_p1, col_p2, col_p3 = st.columns([4, 2, 2])
                        with col_p1:
                            tipo_part = st.radio(
                                "Modalidad de Partida:",
                                ["Catálogo Oficial de mi Área", "Partida Manual Libre", "Servicio No Realizable (DSNR)"],
                                horizontal=True,
                                key=f"tipo_p_{p['id']}"
                            )
                            
                            if tipo_part == "Catálogo Oficial de mi Área":
                                if not servicios_area:
                                    st.warning("No hay servicios catalogados para esta área en la base de datos.")
                                    clave_elegida = None
                                    p_costo_base = 0.0
                                    p_dias_def = 5
                                    desc_final = ""
                                else:
                                    if len(labs_disponibles) > 1:
                                        filtro_lab = st.selectbox(
                                            "🔬 Filtrar por Laboratorio:",
                                            options=["(Todos los laboratorios)"] + labs_disponibles,
                                            key=f"flab_{p['id']}"
                                        )
                                        if filtro_lab != "(Todos los laboratorios)":
                                            servs_filtrados = [s for s in servicios_area if s.get('codigo_laboratorio') == filtro_lab]
                                        else:
                                            servs_filtrados = servicios_area
                                    else:
                                        servs_filtrados = servicios_area

                                    serv_options = {
                                        s['clave_servicio']: f"[{s.get('codigo_laboratorio') or 'GRAL'}] {s['clave_servicio']} - {s['supuesto'][:70]}... (${float(s['costo']):,.2f})"
                                        for s in servs_filtrados
                                    }
                                    def_idx = 0
                                    if p.get('clave_servicio') in serv_options:
                                        def_idx = list(serv_options.keys()).index(p['clave_servicio'])
                                    clave_elegida = st.selectbox(
                                        "Seleccione Servicio del Catálogo (Filtrado por tu Área):",
                                        options=list(serv_options.keys()),
                                        index=def_idx,
                                        format_func=lambda x: serv_options[x],
                                        key=f"serv_{p['id']}"
                                    )
                                    s_info = next((s for s in servs_filtrados if s['clave_servicio'] == clave_elegida), None)
                                    if s_info:
                                        lab_label = f" | 🏢 **Lab:** `{s_info.get('codigo_laboratorio', '')}` - {s_info.get('nombre_laboratorio', '')}" if s_info.get('nombre_laboratorio') else ""
                                        st.caption(f"**Alcance:** {s_info.get('alcance') or 'N/A'}{lab_label}")
                                        p_costo_base = float(s_info['costo'])
                                        p_dias_def = s_info['dias_habiles_defecto']
                                        desc_final = s_info['supuesto']
                            elif tipo_part == "Partida Manual Libre":
                                desc_final = st.text_input("Descripción personalizada del servicio:", value=p['descripcion_servicio'] or "", key=f"man_desc_{p['id']}")
                                p_costo_base = st.number_input("Precio Unitario ($ M.N.):", value=float(p['precio_unitario'] or 0.0), key=f"man_cost_{p['id']}")
                                p_dias_def = 5
                                clave_elegida = "MANUAL"
                            else: # DSNR
                                clave_elegida = "DSNR"
                                desc_final = p['descripcion_equipo']
                                p_costo_base = 0.0
                                p_dias_def = 0
                                motivo_dsnr = st.text_area(
                                    "Motivo Técnico Oficial de No Realización y Canalización:",
                                    value="Lamentamos informarle que este servicio no se realiza en el CENAM. Favor de canalizar este servicio a laboratorios secundarios, actualmente hay muchos que están acreditados.",
                                    key=f"dsnr_txt_{p['id']}"
                                )

                        with col_p2:
                            if tipo_part != "Servicio No Realizable (DSNR)":
                                cant = st.number_input("Cantidad de Servicios:", min_value=1, value=int(p['cantidad'] or 1), key=f"cant_{p['id']}")
                                dias_cal = st.number_input("Días Hábiles (Tiempo cal.):", min_value=1, value=int(p['tiempo_dias_habiles'] or p_dias_def), key=f"dias_{p['id']}")
                            else:
                                cant = 1
                                dias_cal = 0
                                
                        with col_p3:
                            if tipo_part != "Servicio No Realizable (DSNR)":
                                p_total = p_costo_base * cant
                                st.metric("Costo Total Partida", f"${p_total:,.2f}")
                                st.caption(f"Unitario: ${p_costo_base:,.2f} × {cant}")
                            else:
                                p_total = 0.0
                                st.error("Servicio No Realizable (DSNR)")
                                
                        if tipo_part != "Servicio No Realizable (DSNR)":
                            col_com1, col_com2 = st.columns(2)
                            with col_com1:
                                com_ssi = st.text_area("🔒 Comentarios para SSI (Interno - No visible para el cliente):", value=p.get('comentarios_ssi') or "", key=f"cssi_{p['id']}", placeholder="Observaciones técnicas de viabilidad o notas operativas para SSI...")
                            with col_com2:
                                com_cli = st.text_area("📋 Comentarios para Cliente (Visible en Cotización oficial):", value=p.get('comentarios_cliente') or "", key=f"ccli_{p['id']}", placeholder="Condiciones específicas del servicio que se imprimirán en el PDF para el cliente...")
                        else:
                            com_ssi = ""
                            com_cli = ""
                            
                        if st.button("💾 Guardar Partida", key=f"save_p_{p['id']}"):
                            conn = db.get_connection()
                            c = conn.cursor()
                            c.execute("""
                            UPDATE partidas
                            SET es_manual = ?, clave_servicio = ?, descripcion_servicio = ?,
                                tiempo_dias_habiles = ?, cantidad = ?, precio_unitario = ?,
                                precio_total = ?, es_no_realizable = ?, motivo_dsnr = ?,
                                comentarios_ssi = ?, comentarios_cliente = ?, estado_partida = 'COTIZADA'
                            WHERE id = ?
                            """, (
                                1 if tipo_part == "Partida Manual Libre" else 0,
                                clave_elegida, desc_final, dias_cal, cant, p_costo_base, p_total,
                                1 if tipo_part == "Servicio No Realizable (DSNR)" else 0,
                                motivo_dsnr if tipo_part == "Servicio No Realizable (DSNR)" else None,
                                com_ssi, com_cli,
                                p['id']
                            ))
                            conn.commit()
                            conn.close()
                            st.success(f"Partida {p['numero_partida']} guardada con éxito.")
                            st.rerun()
                            
                        st.divider()

                    if st.button("🏁 Aprobar y Regresar Cotización a SSI", key=f"finish_sub_{sol['sub_id']}", type="primary"):
                        conn = db.get_connection()
                        c = conn.cursor()
                        
                        errores_validacion = []
                        
                        # 1. AUTO-GUARDADO Y VALIDACIÓN ESTRICTA DE PRECIOS > 0
                        for p in partidas_at:
                            pid = p['id']
                            modo_k = f"tipo_p_{pid}"
                            modo_val = st.session_state.get(modo_k, "Catálogo Oficial de mi Área" if p.get('clave_servicio') not in ('MANUAL', 'DSNR') else ("Partida Manual Libre" if p.get('es_manual') == 1 else "Servicio No Realizable (DSNR)"))
                            
                            if modo_val == "Catálogo Oficial de mi Área":
                                ssel_k = f"serv_{pid}"
                                s_sel_val = st.session_state.get(ssel_k, p.get('clave_servicio'))
                                s_obj = serv_by_clave.get(s_sel_val)
                                p_costo_val = float(s_obj['costo']) if s_obj else float(p.get('precio_unitario') or 0.0)
                                desc_fin_val = s_obj['supuesto'] if s_obj else (p.get('descripcion_servicio') or "")
                                cant_val = int(st.session_state.get(f"cant_{pid}", p.get('cantidad') or 1))
                                dias_val = int(st.session_state.get(f"dias_{pid}", p.get('tiempo_dias_habiles') or (s_obj['dias_habiles_defecto'] if s_obj else 5)))
                                tot_val = p_costo_val * cant_val
                                es_no_val = 0
                                es_man_val = 0
                                mot_dsnr_val = None
                                
                                if not s_sel_val or s_sel_val not in serv_by_clave:
                                    errores_validacion.append(f"Partida {p['numero_partida']}: No se ha seleccionado un servicio del catálogo.")
                                elif p_costo_val <= 0.0:
                                    errores_validacion.append(f"Partida {p['numero_partida']}: El servicio seleccionado tiene costo $0.00. Debe registrarse un precio mayor a cero.")
                                    
                            elif modo_val == "Partida Manual Libre":
                                desc_fin_val = st.session_state.get(f"man_desc_{pid}", p.get('descripcion_servicio') or "").strip()
                                p_costo_val = float(st.session_state.get(f"man_cost_{pid}", p.get('precio_unitario') or 0.0))
                                cant_val = int(st.session_state.get(f"cant_{pid}", p.get('cantidad') or 1))
                                dias_val = int(st.session_state.get(f"dias_{pid}", p.get('tiempo_dias_habiles') or 5))
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
                                mot_dsnr_val = st.session_state.get(f"dsnr_txt_{pid}", p.get('motivo_dsnr') or "Lamentamos informarle que este servicio no se realiza en el CENAM.")
                                
                            cssi_val = st.session_state.get(f"cssi_{pid}", p.get('comentarios_ssi') or "") if es_no_val == 0 else ""
                            ccli_val = st.session_state.get(f"ccli_{pid}", p.get('comentarios_cliente') or "") if es_no_val == 0 else ""
                            
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
                            
                            st.session_state["flash_msg"] = (
                                "success",
                                f"✅ ¡Respuesta enviada a SSI exitosamente! La cotización Folio **{sol['no_folio']}** ha sido concluida y validada. SSI la consolidará para el cliente."
                            )
                            st.toast(f"Folio {sol['no_folio']} enviado a SSI", icon="📤")
                            st.rerun()

    # ----------------------------------------------------
    # AT PESTAÑA 2: PROGRAMACIÓN DE FECHAS (ETAPA 3)
    # ----------------------------------------------------
    with at_tab2:
        st.subheader("Programación de Fechas de Laboratorio (Servicios con Cotización Aceptada)")
        st.caption("Asigne libremente la fecha de inicio, entrega y límite. La fecha de recepción se calcula automáticamente a 2 días hábiles antes del inicio.")
        
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
        """, (at_actual,))
        pendientes_prog = c.fetchall()
        conn.close()
        
        if not pendientes_prog:
            st.success(f"🎉 No hay servicios pendientes de programar fechas para **{at_actual}**. ¡Todo al día!")
        else:
            for sp in pendientes_prog:
                is_rep = (sp['estado'] == 'REPROGRAMACION')
                b_color = "🔴 REPROGRAMACIÓN SOLICITADA POR CLIENTE" if is_rep else "📅 PROGRAMACIÓN PENDIENTE"
                
                with st.expander(f"Folio: {sp['no_folio']} | Cotización: {sp['no_cotizacion']} | {sp['cliente']} [{b_color}]", expanded=True):
                    if sp.get('orden_compra_cliente'):
                        st.info(f"📄 **Orden de Compra / Oficio del Cliente:** `{sp['orden_compra_cliente']}` | **Aceptada:** `{sp.get('fecha_aceptacion_cotizacion') or 'N/A'}`")
                    if is_rep and sp['motivo_reprogramacion']:
                        st.warning(f"⚠️ **Motivo de reprogramación indicado por el cliente:**\n{sp['motivo_reprogramacion']}", icon="⚠️")
                        
                    conn = db.get_connection()
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
                        
                        # 1. Fecha de Inicio de Calibración
                        with col_f2:
                            def_ini = date.today() + timedelta(days=14)
                            if p['fecha_inicio_calibracion']:
                                try: def_ini = datetime.strptime(p['fecha_inicio_calibracion'], "%Y-%m-%d").date()
                                except: pass
                            f_ini = st.date_input("Fecha Inicio Calibración *:", value=def_ini, key=f"f_ini_{p['id']}")
                            
                            # Sincronización automática: Si AT cambia la fecha de inicio, la recepción se recalcula (-2 días hábiles)
                            prev_ini_k = f"prev_f_ini_{p['id']}"
                            if prev_ini_k in st.session_state and st.session_state[prev_ini_k] != f_ini:
                                f_ini_dt = datetime.combine(f_ini, datetime.min.time())
                                st.session_state[f"f_rec_{p['id']}"] = db.restar_dias_habiles(f_ini_dt, 2).date()
                                d_h = int(p['tiempo_dias_habiles'] or 5)
                                st.session_state[f"f_fin_{p['id']}"] = db.sumar_dias_habiles(f_ini_dt, d_h).date()
                            st.session_state[prev_ini_k] = f_ini
                            
                        # 2. Fecha de Recepción (Automática: 2 días hábiles antes de f_ini, con posibilidad de cambiarse)
                        with col_f1:
                            f_ini_dt = datetime.combine(f_ini, datetime.min.time())
                            f_rec_auto = db.restar_dias_habiles(f_ini_dt, 2).date()
                            if p['fecha_recepcion_equipo']:
                                try: f_rec_auto = datetime.strptime(p['fecha_recepcion_equipo'], "%Y-%m-%d").date()
                                except: pass
                            f_rec = st.date_input("Fecha Recepción Equipo (Automática -2 días hábiles):", value=f_rec_auto, key=f"f_rec_{p['id']}")
                            
                        # 3. Fecha de Entrega / Fin
                        with col_f3:
                            dias_h = int(p['tiempo_dias_habiles'] or 5)
                            f_fin_auto = db.sumar_dias_habiles(f_ini_dt, dias_h).date()
                            if p['fecha_entrega_equipo']:
                                try: f_fin_auto = datetime.strptime(p['fecha_entrega_equipo'], "%Y-%m-%d").date()
                                except: pass
                            f_fin = st.date_input("Fecha Entrega Equipo / Fin *:", value=f_fin_auto, key=f"f_fin_{p['id']}")
                            
                        # 4. Fecha Límite de Aceptación (Vigencia 3 semanas)
                        with col_f4:
                            f_lim_auto = date.today() + timedelta(days=21)
                            if p['fecha_limite_aceptacion']:
                                try: f_lim_auto = datetime.strptime(p['fecha_limite_aceptacion'], "%Y-%m-%d").date()
                                except: pass
                            f_lim = st.date_input("Fecha Límite Aceptación:", value=f_lim_auto, key=f"f_lim_{p['id']}")
                            
                        fechas_por_partida[p['id']] = {
                            "recepcion": f_rec.strftime("%Y-%m-%d"),
                            "inicio": f_ini.strftime("%Y-%m-%d"),
                            "entrega": f_fin.strftime("%Y-%m-%d"),
                            "limite": f_lim.strftime("%Y-%m-%d")
                        }
                        st.write("")
                        
                    if st.button("🚀 Enviar Fechas Programadas a SSI", key=f"btn_send_prog_{sp['sub_id']}", type="primary"):
                        conn = db.get_connection()
                        c = conn.cursor()
                        # Guardar fechas por partida
                        for pid, f_dict in fechas_por_partida.items():
                            c.execute("""
                            UPDATE partidas
                            SET fecha_recepcion_equipo = ?, fecha_inicio_calibracion = ?,
                                fecha_fin_calibracion = ?, fecha_entrega_equipo = ?, fecha_limite_aceptacion = ?
                            WHERE id = ?
                            """, (f_dict['recepcion'], f_dict['inicio'], f_dict['entrega'], f_dict['entrega'], f_dict['limite'], pid))
                            
                        # Guardar fechas generales en sub_solicitud
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
                        
                        # Actualizar estado master si aplica
                        c.execute("UPDATE solicitudes_master SET estado = 'PROGRAMA_PROPUESTO' WHERE id = ?", (sp['master_id'],))
                        conn.commit()
                        conn.close()
                        
                        st.session_state["flash_msg"] = (
                            "success",
                            f"🗓️ ¡Fechas programadas para Folio **{sp['no_folio']}** enviadas a SSI con éxito! La solicitud se remueve de su pantalla y SSI emitirá la propuesta de programa al cliente."
                        )
                        st.toast(f"Fechas programadas enviadas a SSI", icon="🗓️")
                        st.rerun()

    # ----------------------------------------------------
    # AT PESTAÑA 3: SERVICIOS CONFIRMADOS (RESERVAS)
    # ----------------------------------------------------
    with at_tab3:
        st.subheader("Servicios Confirmados y Reservas en Laboratorio")
        st.caption("Consulta operativa de fechas confirmadas para el resguardo y disponibilidad de patrones y personal.")
        
        conn = db.get_connection()
        c = conn.cursor()
        c.execute("""
            SELECT s.id as sub_id, m.no_folio, m.no_cotizacion, m.cliente, m.representante as contacto,
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
            conf_df = pd.DataFrame([{
                "Folio": r['no_folio'],
                "Cotización": r['no_cotizacion'],
                "Cliente": r['cliente'],
                "Fecha Recepción": r['fecha_recepcion_prog'],
                "Fecha Inicio": r['fecha_inicio_prog'],
                "Fecha Entrega": r['fecha_entrega_prog'],
                "Estado": "🔒 RESERVA CONFIRMADA"
            } for r in confirmados])
            st.dataframe(conf_df, width="stretch")
