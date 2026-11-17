"""
=============================================================================
CENAM - Script de Consulta a Base de Datos Supabase (Catálogo y Laboratorios)
=============================================================================
Este programa muestra paso a paso cómo se accede a la API REST de Supabase
utilizando únicamente la biblioteca estándar de Python (sin instalar paquetes extras).
"""

import urllib.request
import urllib.error
import json
import os

# =============================================================================
# PASO 1: Configurar los parámetros de conexión
# =============================================================================
SUPABASE_URL = "https://hgjbvfojjibcwespaxly.supabase.co"
SUPABASE_KEY = "sb_publishable_nxXsrifcSI7BbIk1FDBp1g_j43HtdDU"

# La API REST de Supabase (PostgREST) se ubica en la ruta /rest/v1/
REST_URL = f"{SUPABASE_URL}/rest/v1"

# =============================================================================
# PASO 2: Construir las cabeceras HTTP de autenticación obligatorias
# =============================================================================
# Supabase requiere que la llave pública o de servicio se envíe en:
#   1. El encabezado 'apikey'
#   2. El encabezado 'Authorization' con el prefijo 'Bearer '
#   3. 'Range': para permitir extraer más de los 100 registros predeterminados
HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Accept": "application/json",
    "Range": "0-999"  # Solicita hasta 1000 registros
}

def consultar_tabla(nombre_tabla):
    """
    Función que realiza una petición GET a cualquier tabla expuesta en Supabase.
    """
    endpoint = f"{REST_URL}/{nombre_tabla}?select=*"
    print(f"\n[PASO 3] Consultando endpoint: {endpoint}")
    
    # Crear la solicitud HTTP con las cabeceras requeridas
    peticion = urllib.request.Request(endpoint, headers=HEADERS, method="GET")
    
    try:
        # Enviar la solicitud a través de HTTPS con un tiempo límite de 10 segundos
        with urllib.request.urlopen(peticion, timeout=10) as respuesta:
            codigo_http = respuesta.status
            cuerpo_bytes = respuesta.read()
            datos_json = json.loads(cuerpo_bytes.decode("utf-8"))
            
            print(f"  -> Conexión Exitosa. Código HTTP: {codigo_http}")
            print(f"  -> Total de registros recibidos: {len(datos_json)}")
            return True, datos_json
            
    except urllib.error.HTTPError as error_http:
        # En caso de error HTTP (por ejemplo 401 Unauthorized o 404 Not Found),
        # leemos el mensaje exacto que devuelve el motor PostgreSQL de Supabase.
        codigo = error_http.code
        cuerpo_error = error_http.read().decode("utf-8")
        try:
            error_json = json.loads(cuerpo_error)
        except Exception:
            error_json = cuerpo_error
            
        print(f"  -> Error HTTP {codigo} al consultar la tabla '{nombre_tabla}':")
        print(f"     Detalle de Supabase: {json.dumps(error_json, indent=2, ensure_ascii=False)}")
        return False, error_json

    except urllib.error.URLError as error_red:
        print(f"  -> Error de red o conexión: {error_red}")
        return False, str(error_red)

# =============================================================================
# PASO 4: Ejecución y revisión de ambas tablas
# =============================================================================
def main():
    print("=" * 70)
    print("INICIANDO VERIFICACIÓN PASO A PASO DE ACCESO A SUPABASE")
    print(f"URL Base: {SUPABASE_URL}")
    print("=" * 70)

    # -------------------------------------------------------------------------
    # Prueba 1: Tabla 'catalogo_servicios'
    # -------------------------------------------------------------------------
    print("\n--- 1. CONSULTA A LA TABLA 'catalogo_servicios' ---")
    ok_serv, serv_data = consultar_tabla("catalogo_servicios")
    
    if ok_serv and len(serv_data) > 0:
        print("\n  [ANÁLISIS DE DATOS - CATALOGO_SERVICIOS]")
        primer_registro = serv_data[0]
        print("  Columnas disponibles:")
        for col, val in primer_registro.items():
            print(f"    - {col}: {val}")
            
        # Resumen de laboratorios y divisiones encontrados
        divisiones = set(d.get("division") for d in serv_data if d.get("division"))
        laboratorios = set(d.get("laboratorio") for d in serv_data if d.get("laboratorio"))
        print(f"\n  Divisiones identificadas: {sorted(list(divisiones))}")
        print(f"  Total de Laboratorios distintos en servicios: {len(laboratorios)}")
        print(f"  Muestra de Laboratorios: {sorted(list(laboratorios))[:10]}...")

    # -------------------------------------------------------------------------
    # Prueba 2: Tabla 'laboratorios'
    # -------------------------------------------------------------------------
    print("\n" + "-" * 70)
    print("--- 2. CONSULTA A LA TABLA 'laboratorios' ---")
    ok_lab, lab_data = consultar_tabla("laboratorios")
    
    if ok_lab:
        print("  ¡Lectura de 'laboratorios' exitosa!")
        if lab_data:
            print(f"  Primer registro: {lab_data[0]}")
    else:
        print("\n  [DIAGNÓSTICO DEL FALLO EN 'laboratorios']:")
        print("  La tabla 'laboratorios' existe, pero PostgreSQL deniega el acceso con error 42501.")
        print("  Razón: La API Key proporcionada ('sb_publishable_...') opera bajo el rol 'anon'.")
        print("  Solución: Ejecutar en el SQL Editor de Supabase:")
        print("    GRANT SELECT ON public.laboratorios TO anon;")

    print("\n" + "=" * 70)
    print("PROCESO DE REVISIÓN CONCLUIDO")
    print("=" * 70)

if __name__ == "__main__":
    main()
