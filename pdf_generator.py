import os
from datetime import datetime, date
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether, HRFlowable, PageBreak, Image
)
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT, TA_JUSTIFY

class CenamNumberedCanvas(canvas.Canvas):
    """Canvas de dos pasadas para numeración exacta (Página X de Y) y pie institucional CENAM en todas las páginas."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, total_pages):
        self.saveState()
        # Línea divisoria inferior
        self.setStrokeColor(colors.HexColor('#CBD5E0'))
        self.setLineWidth(0.6)
        self.line(36, 42, 612 - 36, 42)
        
        # Pie de página institucional oficial CENAM
        self.setFont('Helvetica', 6.6)
        self.setFillColor(colors.HexColor('#4A5568'))
        footer_line1 = "km 4,5 carretera a Los Cués, Municipio El Marqués, Querétaro, México, C.P. 76246. Tel. (442) 211-05-00 al 04."
        footer_line2 = "Correo electrónico: DSIservtec@cenam.mx | Página web: https://www.gob.mx/cenam"
        
        self.drawCentredString(612 / 2.0, 31, footer_line1)
        self.drawCentredString(612 / 2.0, 21, footer_line2)
        
        # Paginación a la derecha
        self.setFont('Helvetica-Bold', 7)
        page_str = f"Página {self._pageNumber} de {total_pages}"
        self.drawRightString(612 - 36, 21, page_str)
        self.restoreState()

def get_cenam_logo_path():
    candidate_paths = [
        os.path.join(os.path.dirname(__file__), "static", "logo_cenam.png"),
        os.path.join("nube_segura", "static", "logo_cenam.png"),
        os.path.join("static", "img", "logo_cenam.png"),
        os.path.join(os.path.dirname(__file__), "..", "static", "img", "logo_cenam.png")
    ]
    for p in candidate_paths:
        if os.path.exists(p):
            return p
    return None

def build_cenam_header(titulo_doc, subtitulo=None):
    """Construye el encabezado institucional con logo gráfico oficial CENAM y títulos."""
    logo_path = get_cenam_logo_path()
    logo_flowable = None
    if logo_path:
        try:
            # Tamaño equilibrado: ancho 95 pt, alto 40.4 pt (ratio 2.35)
            logo_flowable = Image(logo_path, width=95, height=40.4)
        except Exception:
            logo_flowable = None
            
    hdr_title_style = ParagraphStyle(
        'HdrTitle',
        fontName='Helvetica-Bold',
        fontSize=11.5,
        leading=13.5,
        textColor=colors.HexColor('#1A365D')
    )
    hdr_doc_style = ParagraphStyle(
        'HdrDoc',
        fontName='Helvetica-Bold',
        fontSize=9.5,
        leading=11.5,
        textColor=colors.HexColor('#8C6D23')
    )
    hdr_sub_style = ParagraphStyle(
        'HdrSub',
        fontName='Helvetica',
        fontSize=7.2,
        leading=9.2,
        textColor=colors.HexColor('#4A5568')
    )
    
    col_text = [
        Paragraph("<b>CENTRO NACIONAL DE METROLOGÍA</b>", hdr_title_style),
        Spacer(1, 1),
        Paragraph(f"<b>{titulo_doc}</b>", hdr_doc_style)
    ]
    if subtitulo:
        col_text.append(Spacer(1, 1))
        col_text.append(Paragraph(subtitulo, hdr_sub_style))
    else:
        col_text.append(Spacer(1, 1))
        col_text.append(Paragraph("Organismo Público Descentralizado | Subdirección de Servicios a la Industria (SSI)", hdr_sub_style))
        
    if logo_flowable:
        data = [[logo_flowable, col_text]]
        col_widths = [105, 435]
    else:
        data = [[col_text]]
        col_widths = [540]
        
    t_hdr = Table(data, colWidths=col_widths)
    t_hdr.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
    ]))
    
    rule = HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#8C6D23'), spaceAfter=8, spaceBefore=4)
    return [t_hdr, rule]

def to_str(val, default=""):
    """Convierte cualquier valor (incluyendo datetime.date de PostgreSQL o None) a str seguro para ReportLab."""
    if val is None or val == "":
        return default
    if isinstance(val, (datetime, date)):
        return val.strftime("%Y-%m-%d")
    return str(val)

def to_float(val, default=0.0):
    """Convierte de forma segura números, strings o Decimal de PostgreSQL a float."""
    if val is None or val == "":
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default

def generate_cotizacion_pdf(solicitud, partidas, filepath):
    doc = SimpleDocTemplate(
        filepath,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=50
    )
    
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=15,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#1A202C')
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#4A5568')
    )
    
    header_label = ParagraphStyle(
        'HeaderLabel',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7.5,
        leading=9.5,
        textColor=colors.HexColor('#2D3748')
    )
    
    header_val = ParagraphStyle(
        'HeaderVal',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.5,
        leading=9.5,
        textColor=colors.HexColor('#1A202C')
    )
    
    tbl_header = ParagraphStyle(
        'TblHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7,
        leading=9,
        alignment=TA_CENTER,
        textColor=colors.white
    )
    
    tbl_cell = ParagraphStyle(
        'TblCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7,
        leading=9,
        textColor=colors.HexColor('#1A202C')
    )
    
    tbl_cell_center = ParagraphStyle(
        'TblCellCenter',
        parent=tbl_cell,
        alignment=TA_CENTER
    )
    
    tbl_cell_right = ParagraphStyle(
        'TblCellRight',
        parent=tbl_cell,
        alignment=TA_RIGHT
    )
    
    notes_style = ParagraphStyle(
        'NotesStyle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=6.5,
        leading=8.5,
        alignment=TA_JUSTIFY,
        textColor=colors.HexColor('#4A5568')
    )
    
    notes_bold = ParagraphStyle(
        'NotesBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7,
        leading=9,
        textColor=colors.HexColor('#2D3748')
    )

    story = []
    
    # 1. Header institucional con logo oficial
    sub_title = f"Subdirección de Servicios a la Industria (SSI) | Clave Área: {solicitud.get('clave_area', '')}" if solicitud.get('clave_area') else "Organismo Público Descentralizado | Subdirección de Servicios a la Industria (SSI)"
    story.extend(build_cenam_header("Cotización de servicios de calibración / medición", sub_title))
    
    # 2. Metadata Box
    data_meta = [
        [
            Paragraph("<b>Cliente :</b>", header_label),
            Paragraph(f"<b>{solicitud.get('cliente', '')}</b>", header_val),
            Paragraph("<b>No. de cotización :</b>", header_label),
            Paragraph(f"<b>{solicitud.get('no_cotizacion', 'PENDIENTE')}</b>", header_val)
        ],
        [
            Paragraph("<b>Representante :</b>", header_label),
            Paragraph(solicitud.get('representante', '') or 'N/A', header_val),
            Paragraph("<b>Versión :</b>", header_label),
            Paragraph(str(solicitud.get('version', 1)), header_val)
        ],
        [
            Paragraph("<b>RFC :</b>", header_label),
            Paragraph(solicitud.get('rfc', '') or 'N/A', header_val),
            Paragraph("<b>No. de folio :</b>", header_label),
            Paragraph(f"<b>{solicitud.get('no_folio', '')}</b>", header_val)
        ],
        [
            Paragraph("<b>Teléfono :</b>", header_label),
            Paragraph(solicitud.get('telefono', '') or 'N/A', header_val),
            Paragraph("<b>No. de solicitud :</b>", header_label),
            Paragraph(f"<b>{solicitud.get('no_solicitud', '')}</b>", header_val)
        ],
        [
            Paragraph("<b>Correo electrónico :</b>", header_label),
            Paragraph(to_str(solicitud.get('correo'), 'N/A'), header_val),
            Paragraph("<b>Fecha emisión :</b>", header_label),
            Paragraph(to_str(solicitud.get('fecha_emision'), str(datetime.now().date())), header_val)
        ],
        [
            Paragraph("<b>País :</b>", header_label),
            Paragraph(to_str(solicitud.get('pais'), 'México'), header_val),
            Paragraph("<b>Vigencia :</b>", header_label),
            Paragraph(to_str(solicitud.get('vigencia'), f"{datetime.now().year}-12-31"), header_val)
        ]
    ]
    
    t_meta = Table(data_meta, colWidths=[90, 180, 100, 170])
    t_meta.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 0.75, colors.HexColor('#CBD5E0')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
        ('BACKGROUND', (0,0), (0,-1), colors.HexColor('#F7FAFC')),
        ('BACKGROUND', (2,0), (2,-1), colors.HexColor('#F7FAFC')),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_meta)
    story.append(Spacer(1, 8))
    
    story.append(Paragraph("<i>Sometemos a su amable consideración la siguiente cotización :</i>", ParagraphStyle(
        'ItalIntro', parent=styles['Normal'], fontName='Helvetica-Oblique', fontSize=7.5, textColor=colors.HexColor('#2D3748')
    )))
    story.append(Spacer(1, 4))
    
    # 3. Partidas Table
    headers_part = [
        Paragraph("Part.", tbl_header),
        Paragraph("Sel.", tbl_header),
        Paragraph("Cant.", tbl_header),
        Paragraph("Descripción del Servicio / Instrumento", tbl_header),
        Paragraph("Marca", tbl_header),
        Paragraph("Modelo", tbl_header),
        Paragraph("No. Serie", tbl_header),
        Paragraph("Tiempo cal.<br/>(Días háb.)", tbl_header),
        Paragraph("Costo unitario $", tbl_header),
        Paragraph("Costo total $", tbl_header)
    ]
    
    data_parts = [headers_part]
    subtotal = 0.0
    
    for idx, p in enumerate(partidas, 1):
        if p.get('es_no_realizable', 0) == 1:
            continue
        cant = int(p.get('cantidad') or 1)
        p_unit = to_float(p.get('precio_unitario'), 0.0)
        p_tot = to_float(p.get('precio_total'), p_unit * cant)
        subtotal += p_tot
        
        desc_full = f"<b>{p.get('descripcion_servicio', '')}</b>"
        if p.get('alcance_solicitado'):
            desc_full += f"<br/><i>Alcance/Puntos:</i> {p.get('alcance_solicitado')}"
        if p.get('id_interno'):
            desc_full += f" | <i>ID:</i> {p.get('id_interno')}"
        if p.get('certificado_anterior'):
            desc_full += f"<br/><i>Certificado anterior:</i> {p.get('certificado_anterior')}"
        coment_cli = p.get('comentarios_cliente')
        if coment_cli and str(coment_cli).strip():
            desc_full += f"<br/><font color='#744210'><b>Condiciones / Comentarios:</b> <i>{coment_cli.strip()}</i></font>"
            
        row = [
            Paragraph(str(idx), tbl_cell_center),
            Paragraph("[  ]", tbl_cell_center),
            Paragraph(str(cant), tbl_cell_center),
            Paragraph(desc_full, tbl_cell),
            Paragraph(p.get('marca', 'N/A') or 'N/A', tbl_cell_center),
            Paragraph(p.get('modelo', 'N/A') or 'N/A', tbl_cell_center),
            Paragraph(p.get('no_serie', 'N/A') or 'N/A', tbl_cell_center),
            Paragraph(str(p.get('tiempo_dias_habiles', 5)), tbl_cell_center),
            Paragraph(f"${p_unit:,.2f}", tbl_cell_right),
            Paragraph(f"${p_tot:,.2f}", tbl_cell_right)
        ]
        data_parts.append(row)
        
    t_parts = Table(data_parts, colWidths=[20, 20, 22, 178, 50, 50, 50, 40, 55, 55])
    t_parts.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1A365D')),
        ('BOX', (0,0), (-1,-1), 0.75, colors.HexColor('#CBD5E0')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 3),
        ('RIGHTPADDING', (0,0), (-1,-1), 3),
    ]))
    story.append(t_parts)
    story.append(Spacer(1, 4))
    
    # 4. Totals Block
    aplica_iva = solicitud.get('aplica_iva', 1)
    iva = (subtotal * 0.16) if aplica_iva else 0.0
    total = subtotal + iva
    
    data_totals = [
        [Paragraph("<b>SubTotal :</b>", header_label), Paragraph(f"<b>${subtotal:,.2f}</b>", tbl_cell_right)],
        [Paragraph(f"<b>I.V.A. ({'16%' if aplica_iva else '0% - Exento'}) :</b>", header_label), Paragraph(f"<b>${iva:,.2f}</b>", tbl_cell_right)],
        [Paragraph("<b>Total (M.N.) :</b>", header_label), Paragraph(f"<b>${total:,.2f}</b>", tbl_cell_right)]
    ]
    t_totals = Table(data_totals, colWidths=[110, 80], hAlign='RIGHT')
    t_totals.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 0.75, colors.HexColor('#CBD5E0')),
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F7FAFC')),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
    ]))
    story.append(t_totals)
    story.append(Spacer(1, 6))
    
    # 5. Instrucciones y Notas
    story.append(Paragraph("<b>INSTRUCCIONES:</b>", notes_bold))
    story.append(Paragraph("Para aceptar la cotización deberá seleccionar las partidas que acepte dando clic o marcando en los cuadros [  ] que aparecen a la izquierda de la descripción de cada partida. La programación con las fechas de recepción y entrega del equipo para los servicios aceptados se le enviará en el transcurso de 4 días hábiles posteriores a su aceptación.", notes_style))
    story.append(Spacer(1, 4))
    
    story.append(Paragraph("<b>OBSERVACIONES:</b>", notes_bold))
    obs_text = """
    El CENAM cotiza conforme a la información proporcionada por el cliente. Al aceptar esta cotización, el cliente asume la responsabilidad de que el servicio cotizado corresponde a su entera satisfacción con el servicio solicitado.<br/>
    Todos los equipos deberán estar identificados con un número de serie o código permanente el cual deberá estar en un lugar que no afecte las características metrológicas del equipo.<br/>
    Los equipos deben ser enviados con baterías nuevas o su fuente de alimentación en buen estado, manuales de operación, cables de conexión (cadena de medición completa) y todos sus accesorios para su correcta operación.<br/>
    Nuestros precios son fijados considerando los costos de producción que se derivan de una valuación de insumos a su costo real de oportunidad, en términos de la fracción II del artículo 26 del Reglamento de la Ley Federal de las Entidades Paraestatales, por lo que el precio actual únicamente es aplicable a los servicios que se brinden durante el presente año.
    """
    story.append(Paragraph(obs_text, notes_style))
    story.append(Spacer(1, 6))
    
    # 6. Cuadro de Consulta Técnica
    data_contacto = [
        [
            Paragraph("<b>Para consulta técnica acerca del servicio favor de indicar con quién nos podemos dirigir:</b>", notes_bold),
            Paragraph("Nombre: _______________________", notes_style),
            Paragraph("Teléfono: ________________", notes_style),
            Paragraph("Correo: _____________________", notes_style)
        ]
    ]
    t_contacto = Table(data_contacto, colWidths=[240, 110, 95, 95])
    t_contacto.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E0')),
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#EDF2F7')),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
    ]))
    story.append(t_contacto)
    
    doc.build(story, canvasmaker=CenamNumberedCanvas)
    return filepath

def generate_programacion_pdf(solicitud, sub_solicitud, partidas_at, tipo='CENAM', filepath='programacion.pdf', rep_legal_cenam=""):
    """
    Genera el formato institucional de PROGRAMACIÓN DE SERVICIOS DE CALIBRACIÓN EN CENAM (o EN SITIO)
    con carátula de fechas, contrato de prestación de servicios, opciones de retorno y firmas.
    """
    partidas_at = [p for p in partidas_at if p.get('aceptada_cliente', 1) == 1 and p.get('es_no_realizable', 0) == 0]
    doc = SimpleDocTemplate(
        filepath,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=50
    )
    
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'ProgTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=15,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#1A202C')
    )
    
    subtitle_style = ParagraphStyle(
        'ProgSub',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#4A5568')
    )
    
    label_bold = ParagraphStyle(
        'ProgLabel',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7.5,
        leading=9.5,
        textColor=colors.HexColor('#2D3748')
    )
    
    val_text = ParagraphStyle(
        'ProgVal',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.5,
        leading=9.5,
        textColor=colors.HexColor('#1A202C')
    )
    
    tbl_hdr = ParagraphStyle(
        'ProgTblHdr',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=6.5,
        leading=8.5,
        alignment=TA_CENTER,
        textColor=colors.white
    )
    
    tbl_txt = ParagraphStyle(
        'ProgTblTxt',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=6.5,
        leading=8.5,
        textColor=colors.HexColor('#1A202C')
    )
    
    tbl_txt_c = ParagraphStyle(
        'ProgTblTxtC',
        parent=tbl_txt,
        alignment=TA_CENTER
    )
    
    tbl_txt_r = ParagraphStyle(
        'ProgTblTxtR',
        parent=tbl_txt,
        alignment=TA_RIGHT
    )
    
    clausula_title = ParagraphStyle(
        'ClausulaTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#1A365D')
    )
    
    legal_text = ParagraphStyle(
        'LegalText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=6,
        leading=7.5,
        alignment=TA_JUSTIFY,
        textColor=colors.HexColor('#2D3748')
    )

    story = []
    
    # Encabezado institucional con logo oficial
    doc_title = "Programación de servicios de calibración en Sitio (IN SITU)" if tipo == 'IN_SITU' else "Programación de servicios de calibración en CENAM"
    area_nombre = sub_solicitud.get('nombre_area', sub_solicitud.get('clave_area', ''))
    sub_title = f"{area_nombre} | Clave: {solicitud.get('clave_area', sub_solicitud.get('clave_area', ''))}"
    story.extend(build_cenam_header(doc_title, sub_title))
    
    # Metadatos Carátula
    fecha_prog = to_str(sub_solicitud.get('fecha_inicio_prog'), str(datetime.now().date()))
    
    data_meta = [
        [
            Paragraph("<b>Cliente :</b>", label_bold),
            Paragraph(f"<b>{solicitud.get('cliente', '')}</b>", val_text),
            Paragraph("<b>Fecha emisión :</b>", label_bold),
            Paragraph(str(datetime.now().date()), val_text)
        ],
        [
            Paragraph("<b>Representante :</b>", label_bold),
            Paragraph(to_str(solicitud.get('representante'), 'N/A'), val_text),
            Paragraph("<b>Vigencia :</b>", label_bold),
            Paragraph(to_str(solicitud.get('vigencia_programacion'), '3 semanas'), val_text)
        ],
        [
            Paragraph("<b>Teléfono :</b>", label_bold),
            Paragraph(to_str(solicitud.get('telefono'), 'N/A'), val_text),
            Paragraph("<b>Correo Electrónico :</b>", label_bold),
            Paragraph(to_str(solicitud.get('correo'), 'N/A'), val_text)
        ],
        [
            Paragraph("<b>De acuerdo a cotización No. :</b>", label_bold),
            Paragraph(f"<b>{solicitud.get('no_cotizacion', 'N/A')}</b>", val_text),
            Paragraph("<b>Versión :</b>", label_bold),
            Paragraph(str(solicitud.get('version', 1)), val_text)
        ],
        [
            Paragraph("<b>Con fecha :</b>", label_bold),
            Paragraph(to_str(solicitud.get('fecha_emision'), str(datetime.now().date())), val_text),
            Paragraph("<b>Área Técnica :</b>", label_bold),
            Paragraph(f"<b>{area_nombre}</b>", val_text)
        ],
        [
            Paragraph("<b>Orden de Compra / Oficio :</b>", label_bold),
            Paragraph(to_str(solicitud.get('orden_compra_cliente'), 'N/A'), val_text),
            Paragraph("<b>Fecha Aceptación :</b>", label_bold),
            Paragraph(to_str(solicitud.get('fecha_aceptacion_cotizacion'), 'N/A'), val_text)
        ]
    ]
    
    t_meta = Table(data_meta, colWidths=[120, 180, 100, 140])
    t_meta.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 0.75, colors.HexColor('#CBD5E0')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
        ('BACKGROUND', (0,0), (0,-1), colors.HexColor('#F7FAFC')),
        ('BACKGROUND', (2,0), (2,-1), colors.HexColor('#F7FAFC')),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_meta)
    story.append(Spacer(1, 6))
    
    story.append(Paragraph("<i>Le informo la programación del (los) servicio(s) correspondientes a esta Área Técnica:</i>", ParagraphStyle('ItalP', parent=styles['Normal'], fontName='Helvetica-Oblique', fontSize=7.5, textColor=colors.HexColor('#2D3748'))))
    story.append(Spacer(1, 4))
    
    # Tabla de Fechas de Programación
    if tipo == 'CENAM':
        headers_prog = [
            Paragraph("Part.", tbl_hdr),
            Paragraph("Aceptada", tbl_hdr),
            Paragraph("Cant.", tbl_hdr),
            Paragraph("Servicio / Instrumento", tbl_hdr),
            Paragraph("P. Unit. $", tbl_hdr),
            Paragraph("P. Total $", tbl_hdr),
            Paragraph("Fecha recepción<br/>equipo", tbl_hdr),
            Paragraph("Fecha inicio<br/>calibración", tbl_hdr),
            Paragraph("Fecha de<br/>entrega", tbl_hdr),
            Paragraph("Fecha límite<br/>aceptación", tbl_hdr)
        ]
        col_w = [18, 32, 18, 162, 45, 45, 55, 55, 55, 55]
    else: # IN SITU
        headers_prog = [
            Paragraph("Part.", tbl_hdr),
            Paragraph("Aceptada", tbl_hdr),
            Paragraph("Cant.", tbl_hdr),
            Paragraph("Servicio / Instrumento", tbl_hdr),
            Paragraph("P. Unit. $", tbl_hdr),
            Paragraph("P. Total $", tbl_hdr),
            Paragraph("Fecha inicio<br/>calibración", tbl_hdr),
            Paragraph("Fecha fin<br/>calibración", tbl_hdr),
            Paragraph("Fecha entrega<br/>resultados", tbl_hdr)
        ]
        col_w = [20, 35, 20, 195, 50, 50, 55, 55, 60]
        
    data_prog = [headers_prog]
    subtotal = 0.0
    
    for idx, p in enumerate(partidas_at, 1):
        cant = int(p.get('cantidad') or 1)
        p_unit = to_float(p.get('precio_unitario'), 0.0)
        p_tot = to_float(p.get('precio_total'), p_unit * cant)
        subtotal += p_tot
        
        desc_txt = f"<b>{p.get('descripcion_servicio', '')}</b>"
        if p.get('id_interno'):
            desc_txt += f"<br/><i>ID:</i> {p.get('id_interno')}"
        if p.get('no_serie'):
            desc_txt += f" | <i>Serie:</i> {p.get('no_serie')}"
            
        f_rec = to_str(p.get('fecha_recepcion_equipo') or sub_solicitud.get('fecha_recepcion_prog'), 'A definir')
        f_ini = to_str(p.get('fecha_inicio_calibracion') or sub_solicitud.get('fecha_inicio_prog'), 'A definir')
        f_fin = to_str(p.get('fecha_fin_calibracion') or p.get('fecha_entrega_equipo') or sub_solicitud.get('fecha_entrega_prog'), 'A definir')
        f_lim = to_str(p.get('fecha_limite_aceptacion') or sub_solicitud.get('fecha_limite_prog'), '3 semanas')
        f_res = to_str(p.get('fecha_entrega_resultados'), f_fin)
        
        if tipo == 'CENAM':
            row = [
                Paragraph(str(idx), tbl_txt_c),
                Paragraph("[ X ]", tbl_txt_c),
                Paragraph(str(cant), tbl_txt_c),
                Paragraph(desc_txt, tbl_txt),
                Paragraph(f"${p_unit:,.2f}", tbl_txt_r),
                Paragraph(f"${p_tot:,.2f}", tbl_txt_r),
                Paragraph(f_rec, tbl_txt_c),
                Paragraph(f_ini, tbl_txt_c),
                Paragraph(f_fin, tbl_txt_c),
                Paragraph(f_lim, tbl_txt_c)
            ]
        else:
            row = [
                Paragraph(str(idx), tbl_txt_c),
                Paragraph("[ X ]", tbl_txt_c),
                Paragraph(str(cant), tbl_txt_c),
                Paragraph(desc_txt, tbl_txt),
                Paragraph(f"${p_unit:,.2f}", tbl_txt_r),
                Paragraph(f"${p_tot:,.2f}", tbl_txt_r),
                Paragraph(f_ini, tbl_txt_c),
                Paragraph(f_fin, tbl_txt_c),
                Paragraph(f_res, tbl_txt_c)
            ]
        data_prog.append(row)
        
    t_prog = Table(data_prog, colWidths=col_w)
    t_prog.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1A365D')),
        ('BOX', (0,0), (-1,-1), 0.75, colors.HexColor('#CBD5E0')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
        ('LEFTPADDING', (0,0), (-1,-1), 2),
        ('RIGHTPADDING', (0,0), (-1,-1), 2),
    ]))
    story.append(t_prog)
    story.append(Spacer(1, 4))
    
    # Totales
    aplica_iva = solicitud.get('aplica_iva', 1)
    iva = (subtotal * 0.16) if aplica_iva else 0.0
    total = subtotal + iva
    
    data_tot = [
        [Paragraph("<b>SubTotal :</b>", label_bold), Paragraph(f"<b>${subtotal:,.2f}</b>", tbl_txt_r)],
        [Paragraph(f"<b>I.V.A. ({'16%' if aplica_iva else '0%'}) :</b>", label_bold), Paragraph(f"<b>${iva:,.2f}</b>", tbl_txt_r)],
        [Paragraph("<b>Total (M.N.) :</b>", label_bold), Paragraph(f"<b>${total:,.2f}</b>", tbl_txt_r)]
    ]
    t_tot = Table(data_tot, colWidths=[90, 80], hAlign='RIGHT')
    t_tot.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E0')),
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F7FAFC')),
        ('TOPPADDING', (0,0), (-1,-1), 1.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 1.5),
    ]))
    story.append(t_tot)
    story.append(Spacer(1, 4))
    
    # Observaciones
    story.append(Paragraph("<b>OBSERVACIONES:</b> Se le informa que los resultados producto de los servicios que brinda el CENAM serán entregados una vez que se acredite el pago correspondiente por el servicio realizado. Los términos y condiciones que rigen la prestación de nuestros servicios son declarados en esta programación.", legal_text))
    story.append(Spacer(1, 6))
    
    # Sección In Situ si aplica
    if tipo == 'IN_SITU':
        dir_sitio = solicitud.get('direccion_servicio_sitio') or 'Instalaciones del cliente según orden de compra'
        cond_acc = solicitud.get('condiciones_acceso_planta') or 'Equipo de protección personal y acceso vehicular/peatonal'
        data_insitu_box = [
            [Paragraph("<b>LUGAR DE REALIZACIÓN DEL SERVICIO:</b>", label_bold), Paragraph(dir_sitio, val_text)],
            [Paragraph("<b>CONDICIONES DE ACCESO A PLANTA:</b>", label_bold), Paragraph(cond_acc, val_text)]
        ]
        t_insitu_box = Table(data_insitu_box, colWidths=[170, 370])
        t_insitu_box.setStyle(TableStyle([
            ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E0')),
            ('BACKGROUND', (0,0), (0,-1), colors.HexColor('#EDF2F7')),
            ('TOPPADDING', (0,0), (-1,-1), 2),
            ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ]))
        story.append(t_insitu_box)
        story.append(Spacer(1, 6))

    # Retorno de Equipos (Para calibración en CENAM)
    if tipo == 'CENAM':
        mod_ret = solicitud.get('modalidad_retorno', 'RECOLECCION_CENAM')
        opc1 = "[ X ]" if mod_ret == 'RECOLECCION_CENAM' else "[   ]"
        opc2 = "[ X ]" if mod_ret == 'MENSAJERIA_CLIENTE' else "[   ]"
        opc3 = "[ X ]" if mod_ret == 'GUIA_PREPAGADA' else "[   ]"
        
        data_retorno = [
            [
                Paragraph("<b>RETORNO DE EQUIPOS:</b> La entrega de equipos y resultados es en las instalaciones del CENAM en días hábiles (lunes a viernes de 9h00 a 16h30, horario de comida 13h00 a 15h00, caja cierra 14h00 a 15h00).", legal_text)
            ],
            [
                Paragraph(f"{opc1} <b>Opción 1:</b> Mi empresa recogerá el equipo en las instalaciones del CENAM.<br/>"
                          f"{opc2} <b>Opción 2:</b> Mi empresa contratará el servicio de mensajería para la recolección en CENAM e informará vía correo al Coordinador de Servicios número de servicio, compañía y fecha.<br/>"
                          f"{opc3} <b>Opción 3:</b> Mi empresa enviará una guía prepagada para el retorno de mi equipo.<br/>"
                          f"<i>En todos los casos el CENAM se deslinda de toda responsabilidad por percances y/o daños que sufra el equipo durante el trayecto de mensajería.</i>", legal_text)
            ]
        ]
        t_ret = Table(data_retorno, colWidths=[540])
        t_ret.setStyle(TableStyle([
            ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E0')),
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F7FAFC')),
            ('TOPPADDING', (0,0), (-1,-1), 2),
            ('BOTTOMPADDING', (0,0), (-1,-1), 2),
            ('LEFTPADDING', (0,0), (-1,-1), 4),
            ('RIGHTPADDING', (0,0), (-1,-1), 4),
        ]))
        story.append(t_ret)
        story.append(Spacer(1, 6))

    # CONTRATO Y CLÁUSULAS LEGALES
    story.append(KeepTogether([
        Paragraph("<b>TÉRMINOS Y CONDICIONES GENERALES - CONTRATO DE PRESTACIÓN DE SERVICIOS</b>", clausula_title),
        Spacer(1, 3),
        Paragraph("""Contrato de prestación de servicios que celebran por una parte el Centro Nacional de Metrología (CENAM), con RFC CNM880126ML4, como prestador del servicio, y por la otra parte el CLIENTE cuyos datos constan en la carátula de este documento (PROGRAMACIÓN), sujetándose a las siguientes:""", legal_text),
        Spacer(1, 2),
        Paragraph("""<b>CLÁUSULAS GENERALES:</b><br/>
        <b>1.</b> El CENAM es un Organismo Público Descentralizado de la Administración Pública Federal, con personalidad jurídica y patrimonio propio coordinado por la Secretaría de Economía, regido por leyes federales.<br/>
        <b>2.</b> El objeto del presente CONTRATO es la prestación del servicio que realizará el CENAM a favor del CLIENTE, descrito en la carátula.<br/>
        <b>3.</b> Las partes reconocen y aceptan obligarse conforme a las condiciones establecidas en este CONTRATO y documentos adicionales.<br/>
        <b>4.</b> El presente instrumento será jurídicamente obligatorio cuando haya sido confirmada su aceptación por el CLIENTE o mediante firma autógrafa o acciones de aceptación tácita.<br/>
        <b>5.</b> Prohibición de cesión de derechos o subcontratación sin autorización previa por escrito.<br/>
        <b>6.</b> CENAM asignará al personal técnico con la capacidad y experiencia requerida.<br/>
        <b>7.</b> El servicio se realizará en el lugar y fecha indicados en la carátula. No se realizará ningún servicio no cotizado, programado y aceptado.<br/>
        <b>8.</b> El CLIENTE pagará de contado y en una sola exhibición el monto total de la contraprestación mediante pago bancario referenciado o electrónico. La entrega de resultados es posterior a la recepción del pago acreditado.<br/>
        <b>9.</b> En moneda nacional conforme a la Ley Monetaria. Para clientes en el extranjero en dólares americanos sin absorción de retenciones locales.<br/>
        <b>10.</b> CENAM se reserva la facultad de otorgar a dependencias públicas un plazo máximo de 30 días para pago.<br/>
        <b>11.</b> Calidad y cumplimiento de condiciones técnicas pactadas.<br/>
        <b>12.</b> Caso fortuito o fuerza mayor debidamente comprobado suspende temporalmente las obligaciones sin responsabilidad.<br/>
        <b>13.</b> Causas de rescisión conforme al Código Civil Federal.<br/>
        <b>14.</b> Para cualquier controversia las partes se someten a la competencia de los tribunales federales con sede en Querétaro.""", legal_text),
        Spacer(1, 4)
    ]))
    
    # Condiciones específicas
    if tipo == 'CENAM':
        condiciones_esp = """<b>CONDICIONES PARA SERVICIOS DE CALIBRACIÓN EN LABORATORIO:</b><br/>
        <b>15.</b> Horario de recepción y entrega de 9:00 a 16:30. Si se entrega después de las 16:30 se recorrerá un día la entrega.<br/>
        <b>16.</b> Si el servicio requiere pago 100% anticipado, el equipo se recibirá únicamente si se tiene el pago acreditado.<br/>
        <b>17.</b> Si el equipo no es entregado en la fecha programada de recepción, CENAM podrá dar por terminado anticipadamente el contrato.<br/>
        <b>18.</b> El equipo debe estar identificado con número de serie permanente y entregarse con cables, manuales, adaptadores y accesorios.<br/>
        <b>19.</b> El cliente podrá cancelar el ingreso dentro de las 24 horas siguientes a la recepción sin cargo alguno.<br/>
        <b>20.</b> Deslinde de responsabilidad por daños en paquetería o mensajería.<br/>
        <b>21.</b> Si se detecta equipo dañado, se suspenderá el servicio cobrando únicamente la etapa realizada.<br/>
        <b>22.</b> Pago dentro de las 2 semanas siguientes a la notificación de conclusión; derecho de retención de equipo como garantía.<br/>
        <b>23.</b> El cliente deberá recoger su equipo en un plazo máximo de tres meses tras concluir el servicio y acreditar el pago.<br/>
        <b>24.</b> Reclamaciones a más tardar 90 días después de concluido el servicio en la Subdirección de Servicios a la Industria (SSI), Edificio T, CENAM, El Marqués, Querétaro."""
    else:
        condiciones_esp = """<b>CONDICIONES PARA SERVICIOS DE CALIBRACIÓN EN SITIO (IN SITU):</b><br/>
        <b>15.</b> El CLIENTE deberá cubrir la partida 'Costo Complementario por Servicio en Sitio' por lo menos 3 semanas antes de la fecha del servicio para emisión de boletos de avión; de lo contrario la programación se cancelará.<br/>
        <b>16.</b> El CLIENTE asegurará que el equipo esté limpio, funcional y con la presencia de su operador calificado.<br/>
        <b>17.</b> Seguridad industrial y horario máximo de 8 horas diarias incluyendo 1 hora de comida.<br/>
        <b>18.</b> El cliente gestionará trámites de acceso a planta y proporcionará equipo de seguridad especial si se requiere.<br/>
        <b>19.</b> Si se niega el acceso al personal del CENAM, se cancelará cobrando viáticos ejercidos y horas invertidas.<br/>
        <b>20.</b> Cancelación con al menos 10 días hábiles de anticipación cubriendo gastos ejercidos.<br/>
        <b>21.</b> Reclamaciones a más tardar a los 90 días siguientes de concluido el servicio ante la Subdirección de Servicios a la Industria."""
        
    story.append(Paragraph(condiciones_esp, legal_text))
    story.append(Spacer(1, 6))
    
    # Datos fiscales y firmas
    story.append(KeepTogether([
        Table([
            [
                Paragraph("<b>Datos Fiscales para facturación :</b>", label_bold),
                Paragraph(f"Razón Social: {solicitud.get('cliente', '')} | RFC: {solicitud.get('rfc', '')} | País: {solicitud.get('pais', 'México')}", val_text)
            ]
        ], colWidths=[150, 390], style=[
            ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E0')),
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#EDF2F7')),
            ('TOPPADDING', (0,0), (-1,-1), 2),
            ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ]),
        Spacer(1, 6),
        Paragraph(f"Leído que fue por las partes el contenido del presente contrato y sabedoras de su alcance legal, lo firman en el Municipio El Marqués, Querétaro, a los {datetime.now().day} días del mes de {datetime.now().strftime('%B')} de {datetime.now().year}.", legal_text),
        Spacer(1, 16),
        Table([
            [
                Paragraph("____________________________________________________<br/><b>EL CLIENTE</b><br/>Nombre y firma del representante o apoderado legal", ParagraphStyle('FirmaCli', parent=styles['Normal'], alignment=TA_CENTER, fontSize=7, leading=9)),
                Paragraph(f"____________________________________________________<br/><b>EL CENAM</b><br/>Representante legal<br/><i>{rep_legal_cenam or ''}</i>", ParagraphStyle('FirmaCenam', parent=styles['Normal'], alignment=TA_CENTER, fontSize=7, leading=9))
            ]
        ], colWidths=[270, 270])
    ]))
    
    doc.build(story, canvasmaker=CenamNumberedCanvas)
    return filepath

def generate_dsnr_pdf(solicitud, partidas_dsnr, direccion_metrologia, filepath):
    doc = SimpleDocTemplate(
        filepath,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=50
    )
    
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=16,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#9B2C2C')
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=13,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#2D3748')
    )
    
    header_label = ParagraphStyle(
        'HeaderLabel',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10,
        textColor=colors.HexColor('#2D3748')
    )
    
    header_val = ParagraphStyle(
        'HeaderVal',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=10,
        textColor=colors.HexColor('#1A202C')
    )
    
    tbl_header = ParagraphStyle(
        'TblHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10,
        alignment=TA_CENTER,
        textColor=colors.white
    )
    
    tbl_cell = ParagraphStyle(
        'TblCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=10,
        textColor=colors.HexColor('#1A202C')
    )
    
    story = []
    
    # 1. Header institucional con logo oficial
    story.extend(build_cenam_header(
        "Respuesta a solicitud de servicio no realizable (DSNR PR)",
        f"{direccion_metrologia or 'Dirección de Metrología'} | Subdirección de Servicios a la Industria (SSI)"
    ))
    
    # 2. Metadata Box
    data_meta = [
        [
            Paragraph("<b>Folio No. :</b>", header_label),
            Paragraph(f"<b>{solicitud.get('no_folio', '')}</b>", header_val),
            Paragraph("<b>Fecha emisión :</b>", header_label),
            Paragraph(to_str(solicitud.get('fecha_emision'), str(datetime.now().date())), header_val)
        ],
        [
            Paragraph("<b>No. Solicitud :</b>", header_label),
            Paragraph(f"<b>{solicitud.get('no_solicitud', '')}</b>", header_val),
            Paragraph("<b>Estado :</b>", header_label),
            Paragraph("<font color='#C53030'><b>NO REALIZABLE (DSNR)</b></font>", header_val)
        ],
        [
            Paragraph("<b>Cliente :</b>", header_label),
            Paragraph(f"<b>{solicitud.get('cliente', '')}</b>", header_val),
            Paragraph("<b>Teléfono :</b>", header_label),
            Paragraph(solicitud.get('telefono', '') or 'N/A', header_val)
        ],
        [
            Paragraph("<b>Representante :</b>", header_label),
            Paragraph(solicitud.get('representante', '') or 'N/A', header_val),
            Paragraph("<b>Correo :</b>", header_label),
            Paragraph(solicitud.get('correo', '') or 'N/A', header_val)
        ]
    ]
    
    t_meta = Table(data_meta, colWidths=[95, 175, 95, 175])
    t_meta.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 0.75, colors.HexColor('#CBD5E0')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
        ('BACKGROUND', (0,0), (0,-1), colors.HexColor('#FFF5F5')),
        ('BACKGROUND', (2,0), (2,-1), colors.HexColor('#FFF5F5')),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_meta)
    story.append(Spacer(1, 12))
    
    # 3. Partidas Table
    headers_part = [
        Paragraph("Part.", tbl_header),
        Paragraph("Descripción del Instrumento Solicitado", tbl_header),
        Paragraph("Motivo Técnico Oficial y Canalización", tbl_header)
    ]
    
    data_parts = [headers_part]
    for idx, p in enumerate(partidas_dsnr, 1):
        desc = f"<b>{p.get('descripcion_equipo', '')}</b>"
        if p.get('marca'):
            desc += f"<br/>Marca: {p.get('marca')}"
        if p.get('modelo'):
            desc += f" | Modelo: {p.get('modelo')}"
        if p.get('no_serie'):
            desc += f" | Serie: {p.get('no_serie')}"
        if p.get('alcance_solicitado'):
            desc += f"<br/>Intervalo/Puntos: {p.get('alcance_solicitado')}"
            
        motivo = p.get('motivo_dsnr') or "Lamentamos informarle que este servicio no se realiza en el CENAM. Favor de canalizar este servicio a laboratorios secundarios, actualmente hay muchos que están acreditados."
        
        data_parts.append([
            Paragraph(str(idx), tbl_cell),
            Paragraph(desc, tbl_cell),
            Paragraph(motivo, tbl_cell)
        ])
        
    t_parts = Table(data_parts, colWidths=[35, 230, 275])
    t_parts.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#C53030')),
        ('BOX', (0,0), (-1,-1), 0.75, colors.HexColor('#CBD5E0')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_parts)
    story.append(Spacer(1, 14))
    
    # 4. Canalización
    story.append(Paragraph(
        "<b>Nota importante de canalización:</b> Para cualquier duda o aclaración técnica sobre esta respuesta, o para consultar el directorio nacional de laboratorios secundarios acreditados ante la Entidad Mexicana de Acreditación (EMA), le sugerimos visitar el portal de la entidad correspondiente o escribir a <i>soporte.clientes@cenam.mx</i>.",
        ParagraphStyle('Aviso', parent=styles['Normal'], fontSize=7.5, leading=10, textColor=colors.HexColor('#4A5568'))
    ))
    story.append(Spacer(1, 20))
    
    # 5. Firma
    dir_firmante = direccion_metrologia or "Dirección de Metrología"
    story.append(KeepTogether([
        Paragraph("<b>ATENTAMENTE</b>", ParagraphStyle('Atte', parent=styles['Normal'], alignment=TA_CENTER, fontName='Helvetica-Bold', fontSize=8)),
        Spacer(1, 15),
        Paragraph(f"<b>{dir_firmante}</b><br/>Centro Nacional de Metrología", ParagraphStyle('Firma', parent=styles['Normal'], alignment=TA_CENTER, fontSize=8, leading=10))
    ]))
    
    doc.build(story, canvasmaker=CenamNumberedCanvas)
    return filepath
