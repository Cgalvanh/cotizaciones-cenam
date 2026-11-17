# Sistema de Cotización de Servicios Metrológicos y DSNR PR (CENAM)

Sistema integral desarrollado para coordinar el flujo de cotizaciones entre la **Ventanilla Central (SSI)**, las **14 Áreas Técnicas (AT)** y los **Especialistas de Laboratorio**, adaptado para operar sin intranet y sobre el canal de correo electrónico.

---

## 🚀 Inicio Rápido

Para iniciar la aplicación en su computadora local:

### Opción 1: Mediante el ejecutable por lotes
Haga doble clic en el archivo:
```text
run_app.bat
```

### Opción 2: Mediante la terminal de comandos (PowerShell / CMD)
```bash
streamlit run app.py
```
La aplicación se abrirá automáticamente en su navegador web en `http://localhost:8501`.

---

## 📁 Estructura del Proyecto

* **`data/areas_tecnicas.csv`**: Archivo externo configurable que contiene la `Clave` y el `Nombre` de las 14 Áreas Técnicas.
* **`data/catalogo_servicios.csv`**: Catálogo completo de servicios oficiales con clave de servicio, descripción, alcance, observaciones, costo en MXN y la columna clave **`Clave_Area`** para restringir la selección exclusiva al área competente.
* **`database.py`**: Motor de persistencia SQLite local (`cotizaciones_cenam.db`) que gestiona folios consecutivos anuales, solicitudes, sub-solicitudes, partidas y bitácora de consultas a especialistas (ISO 17025).
* **`pdf_generator.py`**: Generador de documentos oficiales en PDF idénticos a los formatos institucionales mediante `ReportLab` (Cotización Formal con IVA y desglose de partidas, y Oficio de Dictamen de Servicio No Realizable DSNR PR).
* **`app.py`**: Aplicación interactiva con perfiles diferenciados para SSI y las 14 Áreas Técnicas.

---

## ⚙️ Reglas de Negocio Implementadas

1. **Carga Dinámica de Áreas**: El listado de ATs se lee directamente desde `data/areas_tecnicas.csv`.
2. **Catálogo Clasificado por Área**: Al seleccionar su Área Técnica, el Asesor Técnico (AT) **solo puede ver y elegir los servicios que pertenecen a su clave de área**.
3. **No. de Solicitud**: Generado por SSI al recibir el correo del cliente.
4. **No. de Folio**: Consecutivo anual unívoco que acompaña todo el expediente; el **DSNR PR utiliza este mismo No. de Folio**.
5. **No. de Cotización**: Generado por SSI de forma consecutiva **únicamente cuando la cotización está aprobada y lista para salir**.
6. **División y Consolidación (Multidisciplinaria)**: SSI divide solicitudes con equipos de diferentes magnitudes entre las ATs correspondientes y las consolida en un solo documento para el cliente.
7. **Servicios IN SITU**: Se gestionan en cotizaciones independientes con viáticos.
8. **Partidas Mixtas**: Generación de documentos oficiales separados (Cotización formal por lo viable y DSNR PR por lo no realizable).
9. **Días Hábiles**: El AT define y valida los días hábiles (`Tiempo cal.`).
10. **Partidas Manuales**: El AT puede agregar partidas libres con descripción, importe y días para servicios especiales.
11. **Tratamiento Fiscal (IVA Extranjero)**: Detección automática del país del cliente con propuesta a SSI para exentar el 16% de IVA.
12. **SLA y Especialistas**: Plazo máximo de 3 días hábiles con semáforo de tiempo, reasignación de especialista y archivo de respuesta técnica para auditorías.
13. **Devolución por Área Incorrecta**: El AT puede pulsar *"Devolver a SSI (No Corresponde)"* indicando motivo y área sugerida sin cotizar.
