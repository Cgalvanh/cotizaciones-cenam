import csv
import unicodedata

def clean_text(s):
    if not s:
        return ""
    nkfd = unicodedata.normalize('NFKD', s)
    return "".join([c for c in nkfd if not unicodedata.combining(c)]).lower()

with open("c:/Users/cgalvan/Documents/antigravity/jolly-galileo/scripts/build_catalog.py", "r", encoding="utf-8") as f:
    orig_code = f.read()

# Let's replace the classify_service function with a much more accurate one
new_classify = '''
def classify_service(supuesto, alcance, obs):
    text = clean_text(supuesto + " " + alcance + " " + obs)
    es_in_situ = ("en sitio" in text or "in situ" in text or "pista de prueba" in text)
    
    # 01 Dimensional
    if any(k in text for k in [
        "bloque patron", "autocolimador", "nivel electronico", "nivel de burbuja", 
        "longitud de onda nominal de 633", "escala de vidrio", "escalas de vidrio", 
        "maquinas de medicion por coordenadas", "cmm", "regla graduada", "reglas graduadas", 
        "rugosimetro", "rugosimetros", "anillos patron", "anillo patron", "patron roscado", 
        "redondez", "cilindricidad", "esfera patron", "perpendicularidad", "caliper", 
        "tetraedro", "placa de esferas", "nexcera", "planitud", "panel optico", "escuadra", 
        "escuadras", "rectitud", "maestro de longitudes", "maestros de longitudes", 
        "barra de esferas", "barras patron", "patron de escalon", "patron de rugosidad", 
        "patron gom", "radio de esfera", "artefacto por cota", "regla a pasos koba"
    ]):
        return "AT-01", es_in_situ

    # 04 Tiempo y Frecuencia
    if any(k in text for k in [
        "relojes atomicos", "patrones de frecuencia", "oscilador", "contador de frecuencia", 
        "contadores de frecuencia", "frecuencimetro"
    ]):
        return "AT-04", es_in_situ

    # 05 Termometria y Humedad
    if any(k in text for k in [
        "humedad relativa", "punto de rocio", "humedad en granos", "termometro de radiacion", 
        "fuente de radiacion", "termopar", "resistencia de platino", "sprt", "termometro digital",
        "temperatura de radiancia"
    ]):
        return "AT-05", es_in_situ

    # 06 Optica y Radiometria
    if any(k in text for k in [
        "potencia optica", "otdr", "fuente laser", "espectro optico", "dispersion cromatica", 
        "fotodetector", "irradiancia espectral", "temperatura de color", "espectrorradiometro", 
        "coordenadas de cromaticidad", "intensidad luminosa", "luxometro", "iluminancia", 
        "luminancia", "responsividad fotometrica", "flujo luminoso", "piranometro", 
        "radiometro laser", "luz ultravioleta", "led uv", "dosis de radiacion ultravioleta", 
        "espectrofotometro", "oxido de holmio", "oxido de didimio", "patron de color", 
        "densidad optica neutra", "colorimetro", "refractometro", "polarimetro", 
        "medicion espectrofotometrica"
    ]):
        return "AT-06", es_in_situ

    # 07 Masa y Densidad
    if any(k in text for k in [
        "pesa cilindrica", "pesa individual", "pesas normalizadas", "densimetro", 
        "volumen de solidos", "densidad de un solido", "densidad de liquidos", 
        "instrumentos para pesar de mediano alcance"
    ]):
        return "AT-07", es_in_situ

    # 09 Flujo y Volumen
    if any(k in text for k in [
        "volumetrico", "volumetricos", "pipeta", "pipetas", "matraz", "matraces", "bureta", "buretas", 
        "picnometro", "picnometros", "caudal", "flujo de gas", "flujo de liquidos", 
        "orificio critico", "autotanque", "autotanques", "pemex logistica", 
        "probador compacto", "patron nacional de flujo", "toberas"
    ]):
        return "AT-09", es_in_situ

    # 11 Dureza y Materiales
    if any(k in text for k in ["dureza", "rockwell"]):
        return "AT-11", es_in_situ

    # 12 Quimica y Gases
    if any(k in text for k in [
        "meb", "poliestireno", "frx", "alcoholimetro", "alcoholimetros", "particula", 
        "analizador especifico de gases", "o2", "co,", "oxido nitrico", "dioxido de azufre", 
        "monoxido de carbono", "divisor de gases", "divisores de gases", "tubos capilares", "explosimetro", "explosimetros"
    ]):
        return "AT-12", es_in_situ

    # 13 Fisicoquimica
    if any(k in text for k in ["viscosimetro", "calorimetria", "dsc", "temperatura de fusion de in"]):
        return "AT-13", es_in_situ

    # 02 Electrica (Calibrador multifunción, multímetros, capacitores, inductores, resistores, zener, potencia baja frec)
    if any(k in text for k in [
        "capacit", "induct", "multimetro", "diodo zener", "resistencia electrica", 
        "resistores patron", "decadas de resistencia", "teraohmetro", "tension electrica continua", 
        "corriente electrica continua", "corriente electrica alterna", "tvc", "tcc", "termoconvertidores", 
        "calibrador multifunciones", "tension electrica de 1 mv", "potencia electrica", "energia electrica",
        "angulo de fase", "tension electrica alterna"
    ]):
        return "AT-02", es_in_situ

    # 03 Radiofrecuencia y Microondas
    if any(k in text for k in [
        "coaxial", "atenuador", "dispersion", "terminaciones coaxiales", 
        "suministro electrico (rase)", "rase", "descargas electrostaticas", 
        "factor de calibracion (cf)", "salida de referencia de alta exactitud", 
        "potencia electromagnetica", "potencia en af", "tension electrica en radiofrecuencias",
        "tension electrica en rf", "voltmetro de rf", "termistor", 
        "abrazaderas de absorcion", "corneta", "minibicon", "gaussmetro", 
        "teslametro", "sensor de potencia", "medidor de potencia", "generador de senal",
        "generador de niveles de tension"
    ]):
        return "AT-03", es_in_situ

    # 08 Fuerza y Presion
    if any(k in text for k in [
        "manometro", "manometros", "balanza de presion", "balanzas de presion", "vacuometro", "vacuometros", 
        "par torsional", "torquimetro", "fuerza de alta exactitud", "medicion de fuerza", 
        "equipos de medicion de fuerza", "sistema de fuerza", "sistema de expansion estatica", 
        "amplificador digital"
    ]):
        return "AT-08", es_in_situ

    # 10 Vibraciones y Acustica
    if any(k in text for k in [
        "vibracion", "vibraciones", "acelerometro", "acelerometros", "martillo de impacto", 
        "martillos de impacto", "pendulo", "pendulos", "vibrometro", "vibrometros", "ultrasonido", 
        "ultrasonico", "ultrasonica", "potencia sonora", "detector de fuga", "detectores de fuga", 
        "detector ultrasonico", "hidrofono", "hidrofonos", "espesor", "espesores", "cinemometro", 
        "cinemometros", "rotor", "rotores", "tacometro", "tacometros", "estroboscopica", 
        "estroboscopicas", "microfono", "microfonos", "pistofono", "pistofonos", "sonometro", 
        "sonometros", "audiometro", "audiometros", "dosimetro", "dosimetros", "acoplador acustico", 
        "acopladores acusticos", "transductores de velocidad", "transductores de fuerza", 
        "transductores de desplazamiento", "acondicionadores", "mastoides artificiales", 
        "ciguenales", "mesas de vibracion", "excitadores", "analizador de vibracion", 
        "analizadores de vibracion", "medidores de vibracion", "fantoma", "puntos de soldadura", 
        "bloque de referencia para ultrasonido", "nom-024-stps", "unidad rastreadora",
        "filtros de banda", "velocidad lineal", "excitacion", "absorcion y reflexion acustica",
        "calibradores acusticos"
    ]):
        return "AT-10", es_in_situ

    # Default to 14 if in situ or special
    return "AT-14", es_in_situ
'''

# Replace classify_service
start_def = orig_code.find("def classify_service(supuesto, alcance, obs):")
end_def = orig_code.find("lines = raw_catalog_text.strip().splitlines()")

new_code = orig_code[:start_def] + new_classify.strip() + "\n\n" + orig_code[end_def:]

with open("c:/Users/cgalvan/Documents/antigravity/jolly-galileo/scripts/build_catalog.py", "w", encoding="utf-8") as f:
    f.write(new_code)
print("Updated scripts/build_catalog.py successfully!")
