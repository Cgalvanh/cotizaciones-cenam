import re

def parse_solicitud_text(text):
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
    
    # Extraer Solicitud y Folio si vienen en el encabezado
    m_sol = re.search(r"(?:No\.?\s*de\s*solicitud|Solicitud)\s*[:\.]?\s*([0-9A-Za-z_-]*PR|[0-9]{5,})", text, re.IGNORECASE)
    if m_sol:
        data["no_solicitud"] = m_sol.group(1).strip()
        
    m_fol = re.search(r"(?:No\.?\s*de\s*folio|Folio)\s*[:\.]?\s*([0-9A-Za-z_-]+PR|[0-9]+-[0-9]+[A-Za-z]*)", text, re.IGNORECASE)
    if m_fol:
        data["no_folio"] = m_fol.group(1).strip()
        
    # Datos del solicitante
    m_cont = re.search(r"Nombre del contacto\s*:\s*(.+)", text, re.IGNORECASE)
    if m_cont:
        data["contacto"] = m_cont.group(1).strip()
        
    m_emp = re.search(r"Nombre de la empresa\s*:\s*(.+)", text, re.IGNORECASE)
    if m_emp:
        data["empresa"] = m_emp.group(1).strip()
        
    m_tel = re.search(r"Tel[eé]fono\s*:\s*(.+)", text, re.IGNORECASE)
    if m_tel:
        data["telefono"] = m_tel.group(1).strip()
        
    m_rfc = re.search(r"RFC\s*:\s*(.+)", text, re.IGNORECASE)
    if m_rfc:
        data["rfc"] = m_rfc.group(1).strip()
        
    m_pais = re.search(r"Pa[ií]s\s*:\s*(.+)", text, re.IGNORECASE)
    if m_pais:
        data["pais"] = m_pais.group(1).strip()
        
    m_mail = re.search(r"Correo electr[oó]nico\s*:\s*(.+)", text, re.IGNORECASE)
    if m_mail:
        data["correo"] = m_mail.group(1).strip()
        
    # Instrumentos
    # Separar por "Descripción del instrumento:"
    parts = re.split(r"(?:^|\n)\s*Descripci[oó]n del instrumento\s*:\s*", text, flags=re.IGNORECASE)
    if len(parts) > 1:
        for p in parts[1:]:
            lines = p.strip().split("\n")
            desc = lines[0].strip()
            
            def extract_val(pattern):
                m = re.search(pattern, p, re.IGNORECASE)
                return m.group(1).strip() if m else ""
                
            cert = extract_val(r"Certificado anterior[^:]*:\s*(.+)")
            marca = extract_val(r"Marca\s*:\s*(.+)")
            modelo = extract_val(r"Modelo\s*:\s*(.+)")
            serie = extract_val(r"N[uú]mero de serie\s*:\s*(.+)")
            magnitud = extract_val(r"Magnitud a calibrar\s*:\s*(.+)")
            intervalo = extract_val(r"Intervalo[^:]*:\s*(.+)")
            exactitud = extract_val(r"Exactitud[^:]*:\s*(.+)")
            id_interno = extract_val(r"Identificaci[oó]n interna[^:]*:\s*(.+)")
            condiciones = extract_val(r"Caracter[ií]sticas especiales[^:]*:\s*(.+)")
            
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
                "condiciones": condiciones
            })
            
    return data

# Prueba con el texto provisto por el usuario
sample = """SOLICITUD DE COTIZACIÓN DE SERVICIO DE CALIBRACIÓN. Solicitud 2026009PR.        Folio 0009-2026PR
Estimado cliente:
Con el fin de atender su solicitud de calibración, agradecemos completar la siguiente información y enviarla por correo.
1. Datos del solicitante
Nombre del contacto: ROSA DE LA CRUZ
Nombre de la empresa: SEÑALIZACION Y CONTROL DEL SURESTE
Teléfono: 938 105 7208
RFC: SCS-121208-QK4
País: MÉXICO
Correo electrónico: compras@secont.mx
2. Información del instrumento a calibrar
Descripción del instrumento: Regla de cristal
Certificado anterior o número de equipo CENAM (si aplica): CNM-CC-740-563/2024
Marca: Mitutoyo
Modelo: 172-116
Número de serie: 28719
Magnitud a calibrar: Dimensional 
Intervalo de medición y/o puntos en los que requiere la calibración: (0 a 50) mm
Exactitud o clase nominal del equipo:
Identificación interna del equipo: PR-D-17
Características especiales o condiciones particulares de calibración:
Descripción del instrumento: Regla de cristal
Certificado anterior o número de equipo CENAM (si aplica): CNM-CC-740-579/2024
Marca: Mitutoyo
Modelo: HL2-300
Número de serie: 105092
Magnitud a calibrar: Dimensional 
Intervalo de medición y/o puntos en los que requiere la calibración: (0 a 300) mm
Exactitud o clase nominal del equipo:
Identificación interna del equipo: PR-D-18
Características especiales o condiciones particulares de calibración:
Descripción del instrumento: Retícula de resolución
Certificado anterior o número de equipo CENAM (si aplica): CNM-CC-740-589/2024
Marca: Edmund optics
Modelo: USAF 1951 1X
Número de serie: 38257
Magnitud a calibrar: Dimensional
Intervalo de medición y/o puntos en los que requiere la calibración:
Exactitud o clase nominal del equipo:
Identificación interna del equipo: PR-D-19
Características especiales o condiciones particulares de calibración:
Descripción del instrumento: Retícula angular
Certificado anterior o número de equipo CENAM (si aplica): CNM-CC-740-618/2024
Marca: Edmund optics
Modelo: AA103E
Número de serie: 51021
Magnitud a calibrar: Dimensional
Intervalo de medición y/o puntos en los que requiere la calibración: (0 a 360°)
Exactitud o clase nominal del equipo:
Identificación interna del equipo: PR-D-20
Características especiales o condiciones particulares de calibración:
"""

res = parse_solicitud_text(sample)
print("Folio:", res["no_folio"])
print("Solicitud:", res["no_solicitud"])
print("Cliente:", res["empresa"])
print("Contacto:", res["contacto"])
print("Instrumentos extraídos:", len(res["instrumentos"]))
for i, inst in enumerate(res["instrumentos"]):
    print(f" {i+1}. {inst['descripcion']} | Marca: {inst['marca']} | Modelo: {inst['modelo']} | Serie: {inst['serie']} | ID: {inst['id_interno']}")
