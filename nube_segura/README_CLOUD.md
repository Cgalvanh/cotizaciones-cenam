# Sistema en Nube Segura (CENAM) - Guía de Arquitectura y Despliegue

Esta versión está completamente aislada y preparada para ejecutarse en **Google Cloud Run** y conectarse a **Supabase (PostgreSQL con Cifrado AES-256 y RLS)**.

---

## 🛡️ Características de Seguridad Implementadas

1. **Arquitectura Zero Trust con Control de Acceso por Rol (RBAC)**:
   * Pantalla de inicio de sesión obligatoria con credenciales institucionales `@cenam.mx`.
   * Contraseñas protegidas mediante funciones criptográficas con `salt`.
   * **Aislamiento por Área Técnica**: El Asesor Técnico que inicia sesión solo tiene acceso a las solicitudes de su especialidad (`AT-01`, `AT-02`, etc.) y solo puede elegir servicios de su clave de área.
2. **Bitácora de Auditoría Inmutable (Audit Trail)**:
   * Cada acción (inicio de sesión, creación de folio, consulta a especialista, reasignación, cotización emitida) se registra con usuario, fecha, hora y detalle técnico.
3. **Contenedor Seguro (Hardened Dockerfile)**:
   * Ejecución bajo usuario no-root (`appuser`), sin privilegios de administrador.
   * Cero puertos innecesarios expuestos; adaptado para el puerto dinámico de Google Cloud Run (`$PORT`).
4. **Base de Datos Híbrida Inteligente**:
   * Si se define la variable `DATABASE_URL`, se conecta a PostgreSQL en la nube (Supabase / Cloud SQL) mediante túnel cifrado obligatorio `sslmode=require`.
   * Si se ejecuta en modo local o de prueba sin variables de entorno, utiliza una base de datos segura de respaldo.

---

## 👥 Credenciales de Acceso Precargadas para Pruebas

| Perfil / Área | Correo Electrónico | Contraseña | Rol y Permisos |
| :--- | :--- | :--- | :--- |
| **Ventanilla Central (SSI)** | `ssi@cenam.mx` | `Cenam2026*` | Crea folios, divide solicitudes, reasigna y consolida |
| **AT Eléctrica** | `at.electrica@cenam.mx` | `Cenam2026*` | Exclusivo `AT-02 - Metrología Eléctrica` |
| **AT Dimensional** | `at.dimensional@cenam.mx` | `Cenam2026*` | Exclusivo `AT-01 - Metrología Dimensional` |
| **AT Acústica y Vibraciones** | `at.acustica@cenam.mx` | `Cenam2026*` | Exclusivo `AT-10 - Vibraciones y Acústica` |
| **AT Presión y Fuerza** | `at.presion@cenam.mx` | `Cenam2026*` | Exclusivo `AT-08 - Fuerza y Presión` |
| **Administrador** | `admin@cenam.mx` | `Cenam2026*` | Supervisión general y auditoría |

---

## 🚀 Cómo Desplegar en Google Cloud Run (En 3 Pasos)

### Paso 1: Crear la Base de Datos en Supabase (Gratuito y Cifrado)
1. Inicie sesión en [supabase.com](https://supabase.com) y cree un nuevo proyecto (ej. `cenam-servicios`).
2. Abra el **SQL Editor** en el panel de Supabase y ejecute el contenido del archivo:
   ```text
   nube_segura/supabase_schema.sql
   ```
3. Copie la cadena de conexión URI (Settings > Database > Connection URI) que tiene el formato:
   ```text
   postgresql://postgres.[ID]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres?sslmode=require
   ```

### Paso 2: Desplegar en Google Cloud Run con la CLI de gcloud
Desde la carpeta raíz del proyecto, ejecute en su terminal:

```bash
cd nube_segura

gcloud run deploy cenam-cotizador \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars DATABASE_URL="[PEGA_AQUI_LA_CADENA_DE_SUPABASE]"
```

*Google Cloud Run compilará el contenedor Docker, configurará el certificado SSL automático con HTTPS y le entregará una URL segura lista para compartir con SSI y las 14 ATs.*

---

## 💻 Prueba Local de la Versión Nube Segura

Para probar la versión segura en su propia computadora antes de subirla a la nube:
1. Haga doble clic en el archivo [run_nube_segura.bat](file:///c:/Users/cgalvan/Documents/antigravity/jolly-galileo/run_nube_segura.bat).
2. Se abrirá la pantalla de autenticación en su navegador web. Inicie sesión con cualquiera de las cuentas de demostración indicadas en la tabla anterior.
