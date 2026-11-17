import re
import os
import io
import zipfile
import xml.etree.ElementTree as ET

def extract_text_from_docx(file_source):
    """
    Extrae texto plano preservando orden de párrafos y celdas de un archivo DOCX oficial de CENAM.
    file_source puede ser una ruta (str), bytes, o un objeto tipo stream (BytesIO / UploadedFile).
    No requiere librerías externas (utiliza zipfile y xml.etree.ElementTree estándar de Python).
    """
    if file_source is None:
        return ""
    
    stream = file_source
    if isinstance(file_source, (str, os.PathLike)):
        with open(file_source, 'rb') as f:
            stream = io.BytesIO(f.read())
    elif isinstance(file_source, bytes):
        stream = io.BytesIO(file_source)
    elif hasattr(file_source, 'read'):
        content = file_source.read()
        if hasattr(file_source, 'seek'):
            try:
                file_source.seek(0)
            except Exception:
                pass
        stream = io.BytesIO(content)

    try:
        with zipfile.ZipFile(stream) as z:
            xml_content = z.read('word/document.xml')
        tree = ET.fromstring(xml_content)
        paragraphs = []
        for p in tree.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p'):
            texts = [t.text for t in p.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t') if t.text]
            if texts:
                paragraphs.append(''.join(texts))
        return '\n'.join(paragraphs)
    except Exception as e:
        return ""

def sugerir_area_por_magnitud_y_texto(magnitud, descripcion):
    """Determina la clave de Área Técnica / División Oficial CENAM (410, 420, 510, 520, 710, 720, 730, 740, etc.)."""
    mag = (magnitud or "").strip().lower()
    desc = (descripcion or "").strip().lower()
    t = f"{mag} {desc}"
    
    if any(k in t for k in ["dimensional", "longitud", "bloque", "cmm", "rugosi", "esfera", "redondez", "vernier", "micrometro", "regla", "reticula", "retícula", "angul"]):
        return "740" # División de Metrología Dimensional
    elif any(k in t for k in ["electr", "eléctr", "multimetro", "resistor", "capacit", "induct", "zener", "volt", "corriente", "potencia"]):
        return "410" # División de Metrología Eléctrica
    elif any(k in t for k in ["radiofrecuencia", "rf", "coaxial", "atenuador", "antena", "dispersion", "teslametro", "alta frecuencia"]):
        return "440" # División de Radiofrecuencia y Campos EM
    elif any(k in t for k in ["tiempo", "frecuencia", "reloj", "oscilador", "frecuencimetro"]):
        return "430" # División de Tiempo y Frecuencia
    elif any(k in t for k in ["termo", "temperatura", "humedad", "pirometro", "termopar", "rocio", "rocío"]):
        return "420" # División de Termometría y Humedad
    elif any(k in t for k in ["optica", "óptica", "fotometria", "radiometria", "luxometro", "espectro", "laser", "iluminancia", "lampara", "lámpara"]):
        return "520" # División de Óptica y Radiometría
    elif any(k in t for k in ["masa", "pesa", "balanza", "densidad", "densimetro", "báscula"]):
        return "730" # División de Masa y Densidad
    elif any(k in t for k in ["presion", "presión", "fuerza", "manometro", "torquimetro", "celda"]):
        return "720" # División de Fuerza y Presión
    elif any(k in t for k in ["flujo", "volumen", "caudal", "volumetrico", "pipeta", "matraz", "gas"]):
        return "710" # División de Flujo y Volumen
    elif any(k in t for k in ["acustica", "acústica", "vibracion", "vibración", "acelerometro", "sonometro", "microfono"]):
        return "510" # División de Vibraciones y Acústica
    elif any(k in t for k in ["dureza", "durometro", "impacto", "charpy", "brinell", "rockwell", "vickers"]):
        return "700" # División de Dureza y Alta Exactitud
    elif any(k in t for k in ["quimica", "química", "cromatografia", "espectrometria", "material de referencia", "gas patron"]):
        return "630" # División de Análisis Orgánico y Gases
    elif any(k in t for k in ["fisicoquimica", "fisicoquímica", "ph", "conductividad", "viscosidad", "electrolit"]):
        return "620" # División de Electroquímica y Espectrometría
    elif any(k in t for k in ["in situ", "sitio", "planta", "campo", "en sitio"]):
        return "810" # Subdirección de Servicios a la Industria (SSI / In Situ)
    return "740"

def parse_solicitud_text(text):
    """
    Analiza y extrae la información estructurada del formato Solicitud CENAM PR
    ya sea desde el cuerpo de un correo o texto pegado.
    """
    data = {
        "no_solicitud": None,
        "no_folio": None,
        "contacto": "",
        "empresa": "",
        "telefono": "",
        "rfc": "",
        "pais": "México",
        "correo": "",
        "instrumentos": []
    }
    
    if not text or not isinstance(text, str):
        return data

    # 1. Extraer Solicitud y Folio si vienen en el encabezado
    m_sol = re.search(r"(?:No\.?\s*de\s*solicitud|Solicitud)\s*[:\.]?\s*([0-9A-Za-z_-]*PR|[0-9]{4,})", text, re.IGNORECASE)
    if m_sol:
        data["no_solicitud"] = m_sol.group(1).strip()
        
    m_fol = re.search(r"(?:No\.?\s*de\s*folio|Folio)\s*[:\.]?\s*([0-9A-Za-z_-]+PR|[0-9]+-[0-9]+[A-Za-z]*)", text, re.IGNORECASE)
    if m_fol:
        data["no_folio"] = m_fol.group(1).strip()
        
    # 2. Datos del solicitante (Empresa / Cliente)
    # Buscar patrones de mayor a menor especificidad descartando saludos o machotes vacíos
    empresa_patterns = [
        r"(?:^|\n)\s*Nombre de la empresa\s*[:\.]?\s*([^\n\r]+)",
        r"(?:^|\n)\s*Raz[oó]n Social\s*[:\.]?\s*([^\n\r]+)",
        r"(?:^|\n)\s*(?:Empresa|Cliente)\s*[:\.]?\s*([^\n\r]+)"
    ]
    emp_candidates = []
    for pat in empresa_patterns:
        for m in re.finditer(pat, text, re.IGNORECASE):
            raw = m.group(1).strip()
            # Descartar saludos o instrucciones del formato
            if not raw or any(w in raw.lower() for w in ['estimado', 'agradecemos', 'completar', 'favor de', 'nombre de la empresa']):
                continue
            # Limpiar si vienen etiquetas concatenadas en la misma línea
            for sep in ['Representante:', 'Contacto:', 'Teléfono:', 'Telefono:', 'RFC:', 'Fecha :']:
                if sep.lower() in raw.lower():
                    raw = re.split(re.escape(sep), raw, flags=re.IGNORECASE)[0].strip()
            # Descartar si el valor resultante es solo otra etiqueta
            if raw.lower() in ['rfc:', 'rfc', 'dirección:', 'direccion:', 'fecha:', 'fecha :']:
                continue
            if len(raw) >= 3:
                emp_candidates.append((m.start(), raw))
                
    if emp_candidates:
        emp_candidates.sort(key=lambda x: x[0])
        data["empresa"] = emp_candidates[0][1]

    # Contacto / Representante
    contacto_patterns = [
        r"(?:^|\n)\s*Nombre del contacto\s*[:\.]?\s*([^\n\r]+)",
        r"(?:^|\n)\s*Representante\s*[:\.]?\s*([^\n\r]+)",
        r"(?:^|\n)\s*Contacto\s*[:\.]?\s*([^\n\r]+)"
    ]
    cont_candidates = []
    for pat in contacto_patterns:
        for m in re.finditer(pat, text, re.IGNORECASE):
            raw = m.group(1).strip()
            if not raw or any(w in raw.lower() for w in ['estimado', 'agradecemos', 'completar', 'nombre de la empresa']):
                continue
            for sep in ['Departamento:', 'Teléfono:', 'Telefono:', 'Correo:', 'Email:', 'RFC:', 'Fecha :']:
                if sep.lower() in raw.lower():
                    raw = re.split(re.escape(sep), raw, flags=re.IGNORECASE)[0].strip()
            if raw.lower() in ['legal', 'representante', 'representante legal', 'departamento:', 'departamento', 'teléfono:', 'telefono:', 'correo:', 'email:']:
                continue
            if len(raw) >= 3:
                cont_candidates.append((m.start(), raw))
    if cont_candidates:
        cont_candidates.sort(key=lambda x: x[0])
        data["contacto"] = cont_candidates[0][1]
        
    m_tel = re.search(r"(?:^|\n)\s*Tel[eé]fono\s*[:\.]?\s*([^\n\r]+)", text, re.IGNORECASE)
    if m_tel:
        raw_tel = m_tel.group(1).strip()
        for sep in ['Fax:', 'Correo:', 'RFC:', 'Email:']:
            if sep.lower() in raw_tel.lower():
                raw_tel = re.split(re.escape(sep), raw_tel, flags=re.IGNORECASE)[0].strip()
        data["telefono"] = raw_tel
        
    m_rfc = re.search(r"(?:^|\n)\s*RFC\s*[:\.]?\s*([^\n\r]+)", text, re.IGNORECASE)
    if m_rfc:
        raw_rfc = m_rfc.group(1).strip()
        for sep in ['País:', 'Pais:', 'Dirección:', 'Direccion:', 'Tel:']:
            if sep.lower() in raw_rfc.lower():
                raw_rfc = re.split(re.escape(sep), raw_rfc, flags=re.IGNORECASE)[0].strip()
        data["rfc"] = raw_rfc
        
    m_pais = re.search(r"(?:^|\n)\s*Pa[ií]s\s*[:\.]?\s*([^\n\r]+)", text, re.IGNORECASE)
    if m_pais:
        data["pais"] = m_pais.group(1).strip()
        
    m_mail = re.search(r"(?:^|\n)\s*(?:Correo electr[oó]nico|Correo|Email)\s*[:\.]?\s*([^\n\r]+)", text, re.IGNORECASE)
    if m_mail:
        raw_mail = m_mail.group(1).strip()
        for sep in ['De acuerdo', 'Fax:', 'Tel:']:
            if sep.lower() in raw_mail.lower():
                raw_mail = re.split(re.escape(sep), raw_mail, flags=re.IGNORECASE)[0].strip()
        data["correo"] = raw_mail

    # 3. Instrumentos
    # Separar por "Descripción del instrumento:" o "Partida X:"
    parts = re.split(r"(?:^|\n)\s*(?:Descripci[oó]n del instrumento|Partida\s*\d+|Item\s*\d+|Instrumento\s*\d+)\s*[:\.]?\s*", text, flags=re.IGNORECASE)
    if len(parts) > 1:
        for p in parts[1:]:
            lines = p.strip().split("\n")
            desc = lines[0].strip()
            # Si contiene pie de página final, limpiarlo
            if "Agradecemos proporcionar la información" in desc:
                continue
                
            def extract_val(pattern):
                m = re.search(pattern, p, re.IGNORECASE)
                if m:
                    val = m.group(1).strip()
                    # Cortar si topa con el pie de página
                    if "Agradecemos proporcionar la información" in val:
                        val = val.split("Agradecemos proporcionar")[0].strip()
                    return val
                return ""
                
            cert = extract_val(r"Certificado anterior[^:\n]*:\s*(.*)")
            marca = extract_val(r"Marca\s*:\s*(.*)")
            modelo = extract_val(r"Modelo\s*:\s*(.*)")
            serie = extract_val(r"(?:N[uú]mero de serie|serie)\s*:\s*(.*)")
            magnitud = extract_val(r"Magnitud(?: a calibrar)?[^:\n]*:\s*(.*)")
            intervalo = extract_val(r"Intervalo[^:\n]*:\s*(.*)")
            exactitud = extract_val(r"Exactitud[^:\n]*:\s*(.*)")
            id_interno = extract_val(r"Identificaci[oó]n interna[^:\n]*:\s*(.*)")
            condiciones = extract_val(r"Caracter[ií]sticas especiales[^:\n]*:\s*(.*)")
            
            sug_area = sugerir_area_por_magnitud_y_texto(magnitud, desc)
            
            data["instrumentos"].append({
                "descripcion": desc,
                "certificado_anterior": cert,
                "marca": marca,
                "modelo": modelo,
                "serie": serie,
                "magnitud": magnitud,
                "intervalo": intervalo,
                "exactitud": exactitud,
                "id_interno": id_interno,
                "condiciones": condiciones,
                "clave_area_sugerida": sug_area
            })
            
    return data

def parse_solicitud_docx(file_source):
    """Extrae el texto de un archivo docx y lo estructura."""
    text = extract_text_from_docx(file_source)
    return parse_solicitud_text(text)

def parse_solicitud_input(raw_text=None, file_source=None):
    """
    Función de entrada unificada: analiza ya sea texto directo o un archivo DOCX/TXT.
    """
    if file_source is not None:
        name = getattr(file_source, 'name', '') or (file_source if isinstance(file_source, str) else '')
        if name.lower().endswith('.docx'):
            return parse_solicitud_docx(file_source)
        elif name.lower().endswith('.txt'):
            try:
                if hasattr(file_source, 'read'):
                    txt = file_source.read().decode('utf-8', errors='ignore')
                    if hasattr(file_source, 'seek'):
                        file_source.seek(0)
                    return parse_solicitud_text(txt)
                elif isinstance(file_source, str) and os.path.exists(file_source):
                    with open(file_source, 'r', encoding='utf-8', errors='ignore') as f:
                        return parse_solicitud_text(f.read())
            except Exception:
                pass

    if raw_text:
        return parse_solicitud_text(raw_text)
        
    return parse_solicitud_text("")

