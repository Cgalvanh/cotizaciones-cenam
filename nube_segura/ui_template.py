"""Plantilla HTML5 unificada para Servidor ASGI CENAM."""

INDEX_HTML = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CENAM - Sistema de Servicios Metrológicos</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        :root {
            --cenam-gold: #8A6D3B;
            --cenam-navy: #1E3A8A;
            --cenam-blue: #0284c7;
        }
        * { box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f1f5f9; color: #1e293b; margin: 0; padding: 0; line-height: 1.5; }
        .hidden { display: none !important; }
        .cenam-gold { color: #8A6D3B; }
        .bg-cenam-gold { background-color: #8A6D3B; }
        .border-cenam-gold { border-color: #8A6D3B; }
        .cenam-navy { color: #1E3A8A; }
        .bg-cenam-navy { background-color: #1E3A8A; }
        .max-w-7xl { max-width: 80rem; margin-left: auto; margin-right: auto; }
        .flex { display: flex; }
        .items-center { align-items: center; }
        .items-start { align-items: flex-start; }
        .justify-between { justify-content: space-between; }
        .space-x-2 > * + * { margin-left: 0.5rem; }
        .space-x-3 > * + * { margin-left: 0.75rem; }
        .space-x-4 > * + * { margin-left: 1rem; }
        .space-y-1 > * + * { margin-top: 0.25rem; }
        .space-y-2 > * + * { margin-top: 0.5rem; }
        .space-y-3 > * + * { margin-top: 0.75rem; }
        .space-y-4 > * + * { margin-top: 1rem; }
        .space-y-6 > * + * { margin-top: 1.5rem; }
        .grid { display: grid; }
        .grid-cols-1 { grid-template-columns: repeat(1, minmax(0, 1fr)); }
        @media (min-width: 768px) {
            .md\\:grid-cols-2 { grid-template-columns: repeat(2, minmax(0, 1fr)); }
            .md\\:grid-cols-3 { grid-template-columns: repeat(3, minmax(0, 1fr)); }
            .md\\:grid-cols-4 { grid-template-columns: repeat(4, minmax(0, 1fr)); }
            .md\\:col-span-2 { grid-column: span 2 / span 2; }
        }
        .gap-2 { gap: 0.5rem; }
        .gap-3 { gap: 0.75rem; }
        .gap-4 { gap: 1rem; }
        .bg-white { background-color: #ffffff; }
        .bg-slate-50 { background-color: #f8fafc; }
        .bg-slate-100 { background-color: #f1f5f9; }
        .bg-slate-200 { background-color: #e2e8f0; }
        .bg-slate-300 { background-color: #cbd5e1; }
        .bg-blue-900 { background-color: #1e3a8a; }
        .hover\\:bg-blue-800:hover { background-color: #1e40af; }
        .bg-blue-100 { background-color: #dbeafe; }
        .bg-blue-50 { background-color: #eff6ff; }
        .bg-indigo-900 { background-color: #312e81; }
        .hover\\:bg-indigo-800:hover { background-color: #3730a3; }
        .bg-emerald-100 { background-color: #d1fae5; }
        .bg-emerald-50 { background-color: #ecfdf5; }
        .bg-emerald-700 { background-color: #047857; }
        .hover\\:bg-emerald-800:hover { background-color: #065f46; }
        .bg-amber-100 { background-color: #fef3c7; }
        .bg-amber-50 { background-color: #fffbeb; }
        .bg-red-50 { background-color: #fef2f2; }
        .bg-red-700 { background-color: #b91c1c; }
        .hover\\:bg-red-800:hover { background-color: #991b1b; }
        .text-white { color: #ffffff; }
        .text-blue-900 { color: #1e3a8a; }
        .text-blue-800 { color: #1e40af; }
        .text-blue-700 { color: #1d4ed8; }
        .text-blue-600 { color: #2563eb; }
        .text-slate-900 { color: #0f172a; }
        .text-slate-800 { color: #1e293b; }
        .text-slate-700 { color: #334155; }
        .text-slate-600 { color: #475569; }
        .text-slate-500 { color: #64748b; }
        .text-slate-400 { color: #94a3b8; }
        .text-emerald-800 { color: #065f46; }
        .text-emerald-700 { color: #047857; }
        .text-amber-800 { color: #92400e; }
        .text-red-700 { color: #b91c1c; }
        .text-red-800 { color: #991b1b; }
        .border { border: 1px solid #cbd5e1; }
        .border-b { border-bottom: 1px solid #cbd5e1; }
        .border-b-2 { border-bottom-width: 2px; }
        .border-l { border-left: 1px solid #cbd5e1; }
        .border-l-4 { border-left: 4px solid #ef4444; }
        .border-t { border-top: 1px solid #cbd5e1; }
        .border-slate-100 { border-color: #f1f5f9; }
        .border-slate-200 { border-color: #e2e8f0; }
        .border-slate-300 { border-color: #cbd5e1; }
        .border-blue-900 { border-color: #1e3a8a; }
        .border-transparent { border-color: transparent; }
        .border-dashed { border-style: dashed; }
        .border-2 { border-width: 2px; }
        .rounded { border-radius: 0.25rem; }
        .rounded-md { border-radius: 0.375rem; }
        .rounded-lg { border-radius: 0.5rem; }
        .rounded-xl { border-radius: 0.75rem; }
        .rounded-full { border-radius: 9999px; }
        .p-1 { padding: 0.25rem; }
        .p-1\\:5, .p-1\\.5 { padding: 0.375rem; }
        .p-2 { padding: 0.5rem; }
        .p-2\\:5, .p-2\\.5 { padding: 0.625rem; }
        .p-3 { padding: 0.75rem; }
        .p-4 { padding: 1rem; }
        .p-5 { padding: 1.25rem; }
        .p-6 { padding: 1.5rem; }
        .p-8 { padding: 2rem; }
        .px-2 { padding-left: 0.5rem; padding-right: 0.5rem; }
        .px-2\\:5, .px-2\\.5 { padding-left: 0.625rem; padding-right: 0.625rem; }
        .px-3 { padding-left: 0.75rem; padding-right: 0.75rem; }
        .px-4 { padding-left: 1rem; padding-right: 1rem; }
        .px-5 { padding-left: 1.25rem; padding-right: 1.25rem; }
        .py-0\\:5, .py-0\\.5 { padding-top: 0.125rem; padding-bottom: 0.125rem; }
        .py-1 { padding-top: 0.25rem; padding-bottom: 0.25rem; }
        .py-1\\:5, .py-1\\.5 { padding-top: 0.375rem; padding-bottom: 0.375rem; }
        .py-2 { padding-top: 0.5rem; padding-bottom: 0.5rem; }
        .py-2\\:5, .py-2\\.5 { padding-top: 0.625rem; padding-bottom: 0.625rem; }
        .py-3 { padding-top: 0.75rem; padding-bottom: 0.75rem; }
        .py-6 { padding-top: 1.5rem; padding-bottom: 1.5rem; }
        .pl-3 { padding-left: 0.75rem; }
        .ml-1 { margin-left: 0.25rem; }
        .ml-2 { margin-left: 0.5rem; }
        .mr-1 { margin-right: 0.25rem; }
        .mr-1\\.5 { margin-right: 0.375rem; }
        .mr-2 { margin-right: 0.5rem; }
        .mb-1 { margin-bottom: 0.25rem; }
        .mb-2 { margin-bottom: 0.5rem; }
        .mb-3 { margin-bottom: 0.75rem; }
        .mb-4 { margin-bottom: 1rem; }
        .mb-6 { margin-bottom: 1.5rem; }
        .mt-1 { margin-top: 0.25rem; }
        .mt-3 { margin-top: 0.75rem; }
        .mt-4 { margin-top: 1rem; }
        .mt-12 { margin-top: 3rem; }
        .pb-1 { padding-bottom: 0.25rem; }
        .pb-3 { padding-bottom: 0.75rem; }
        .pt-1 { padding-top: 0.25rem; }
        .text-xs { font-size: 0.75rem; }
        .text-sm { font-size: 0.875rem; }
        .text-base { font-size: 1rem; }
        .text-lg { font-size: 1.125rem; }
        .text-xl { font-size: 1.25rem; }
        .text-4xl { font-size: 2.25rem; }
        .font-bold { font-weight: 700; }
        .font-semibold { font-weight: 600; }
        .font-medium { font-weight: 500; }
        .text-center { text-align: center; }
        .text-right { text-align: right; }
        .text-left { text-align: left; }
        .shadow-sm { box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05); }
        .cursor-pointer { cursor: pointer; }
        .cursor-not-allowed { cursor: not-allowed; }
        .w-full { width: 100%; }
        .w-4 { width: 1rem; }
        .w-1\\.5 { width: 0.375rem; }
        .h-4 { height: 1rem; }
        .h-12 { height: 3rem; }
        .h-1\\.5 { height: 0.375rem; }
        .object-contain { object-fit: contain; }
        .sticky { position: sticky; }
        .top-0 { top: 0; }
        .z-50 { z-index: 50; }
        .inline-flex { display: inline-flex; }
        .block { display: block; }
        .overflow-x-auto { overflow-x: auto; }
        .transition { transition-property: all; transition-timing-function: cubic-bezier(0.4, 0, 0.2, 1); transition-duration: 150ms; }
        table { width: 100%; border-collapse: collapse; }
        input, select, textarea { font-family: inherit; font-size: inherit; }
        button { cursor: pointer; border: none; font-family: inherit; }
        button:disabled { cursor: not-allowed; opacity: 0.6; }
        a { text-decoration: none; }
    </style>
</head>
<body class="bg-slate-100 text-slate-800 font-sans min-h-screen">
    <!-- Barra Superior Institucional -->
    <header class="bg-white border-b border-slate-200 sticky top-0 z-50 shadow-sm">
        <div class="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between">
            <div class="flex items-center space-x-4">
                <img src="/static/cenam_logo.png" alt="CENAM" class="h-12 object-contain" onerror="this.src='/static/img/logo_cenam.png'">
                <div>
                    <h1 class="text-xl font-bold text-slate-900 tracking-tight">Centro Nacional de Metrología</h1>
                    <p class="text-xs text-slate-500 font-medium">Sistema Integral de Cotizaciones y Programación de Calibraciones (SCS)</p>
                </div>
            </div>
            <div class="flex items-center space-x-3">
                <div class="hidden lg:flex items-center space-x-2 mr-2">
                    <a href="/solicitud" target="_blank" class="text-xs bg-amber-50 hover:bg-amber-100 text-amber-900 font-bold px-3 py-1.5 rounded-lg border border-amber-300 transition flex items-center gap-1.5 shadow-sm" title="Abrir Formulario Web de Captura para Clientes">
                        <i class="fa-solid fa-earth-americas text-amber-600"></i> Formulario Clientes
                    </a>
                    <a href="/portal" target="_blank" class="text-xs bg-blue-50 hover:bg-blue-100 text-blue-900 font-bold px-3 py-1.5 rounded-lg border border-blue-200 transition flex items-center gap-1.5 shadow-sm" title="Abrir Portal de Seguimiento y Aprobación">
                        <i class="fa-solid fa-user-shield text-blue-600"></i> Portal Clientes
                    </a>
                </div>
                <div id="role-selector-container" class="bg-slate-100 p-1 rounded-lg flex border border-slate-300">
                    <button id="btn-role-ssi" onclick="setRole('SSI')" class="px-3 py-1.5 rounded-md text-xs font-semibold bg-blue-900 text-white shadow-sm flex items-center gap-1.5 transition">
                        <i class="fa-solid fa-building"></i> Ventanilla SSI
                    </button>
                    <button id="btn-role-at" onclick="setRole('AT')" class="px-3 py-1.5 rounded-md text-xs font-semibold text-slate-600 hover:text-slate-900 flex items-center gap-1.5 transition">
                        <i class="fa-solid fa-microscope"></i> Área Técnica CS-AT
                    </button>
                </div>

                <!-- Barra de Sesión de Usuario -->
                <div id="user-session-bar" class="flex items-center gap-2 pl-3 border-l border-slate-300">
                    <span id="user-badge" class="inline-flex items-center px-2.5 py-1 rounded-md text-xs font-bold bg-blue-50 text-blue-900 border border-blue-200">
                        <i class="fa-solid fa-user-circle mr-1.5 text-blue-700"></i> <span id="user-name-display">Usuario</span>
                    </span>
                    <button onclick="abrirModalLogin()" title="Cambiar usuario o cerrar sesión" class="text-xs bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold px-2.5 py-1 rounded border border-slate-300 transition flex items-center gap-1">
                        <i class="fa-solid fa-arrow-right-from-bracket text-red-600"></i> Salir
                    </button>
                </div>
            </div>
        </div>
    </header>

    <!-- Contenedor Principal -->
    <main class="max-w-7xl mx-auto px-4 py-6">
        
        <!-- ============================================== -->
        <!-- VISTA DE VENTANILLA SSI -->
        <!-- ============================================== -->
        <div id="view-ssi">
            <!-- Pestañas de Navegación SSI -->
            <div class="flex border-b border-slate-300 space-x-2 mb-6 overflow-x-auto pb-1">
                <button onclick="setTabSSI(1)" id="ssi-tab-1" class="px-4 py-2 text-sm font-semibold border-b-2 border-blue-900 text-blue-900 flex items-center gap-2">
                    <i class="fa-solid fa-file-circle-plus"></i> 1. Nueva Solicitud
                </button>
                <button onclick="setTabSSI(2)" id="ssi-tab-2" class="px-4 py-2 text-sm font-semibold border-b-2 border-transparent text-slate-600 hover:text-slate-900 flex items-center gap-2">
                    <i class="fa-solid fa-triangle-exclamation text-amber-600"></i> 2. Devueltas <span id="badge-devueltas" class="ml-1 bg-red-100 text-red-800 px-2 py-0.5 rounded-full text-xs font-bold">0</span>
                </button>
                <button onclick="setTabSSI(3)" id="ssi-tab-3" class="px-4 py-2 text-sm font-semibold border-b-2 border-transparent text-slate-600 hover:text-slate-900 flex items-center gap-2">
                    <i class="fa-solid fa-tags"></i> 3. Emisión Cotización <span id="badge-cotiz" class="ml-1 bg-emerald-100 text-emerald-800 px-2 py-0.5 rounded-full text-xs font-bold">0</span>
                </button>
                <button onclick="setTabSSI(4)" id="ssi-tab-4" class="px-4 py-2 text-sm font-semibold border-b-2 border-transparent text-slate-600 hover:text-slate-900 flex items-center gap-2">
                    <i class="fa-solid fa-calendar-check"></i> 4. Aceptación y Programación <span id="badge-prog" class="ml-1 bg-blue-100 text-blue-900 px-2 py-0.5 rounded-full text-xs font-bold">0</span>
                </button>
                <button onclick="setTabSSI(5)" id="ssi-tab-5" class="px-4 py-2 text-sm font-semibold border-b-2 border-transparent text-slate-600 hover:text-slate-900 flex items-center gap-2">
                    <i class="fa-solid fa-file-contract"></i> 5. Contratos y Confirmación
                </button>
                <button onclick="setTabSSI(6)" id="ssi-tab-6" class="px-4 py-2 text-sm font-semibold border-b-2 border-transparent text-slate-600 hover:text-slate-900 flex items-center gap-2">
                    <i class="fa-solid fa-broom"></i> 6. Mantenimiento
                </button>
            </div>

            <!-- SSI PESTAÑA 1: NUEVA SOLICITUD (REVISIÓN Y ASIGNACIÓN PREVIA) -->
            <div id="ssi-panel-1" class="space-y-6">
                <!-- Sección 1.1 Carga Rápida / Pegado de Texto -->
                <div class="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
                    <div class="flex justify-between items-start mb-2">
                        <div>
                            <h2 class="text-lg font-bold text-slate-900 flex items-center gap-2">
                                <i class="fa-solid fa-cloud-arrow-up text-blue-900"></i> Carga Inteligente de Solicitud (Cero Transcripción)
                            </h2>
                            <p class="text-sm text-slate-600">
                                Suba el oficio o formato Word (.docx/.txt) enviado por el cliente o pegue el texto del correo recibido. Los datos serán extraídos para que usted los <strong>revise, clasifique y asigne por Área Técnica antes de turnar</strong>.
                            </p>
                        </div>
                    </div>
                    
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
                        <div class="border-2 border-dashed border-slate-300 rounded-xl p-6 text-center hover:border-blue-900 transition bg-slate-50">
                            <i class="fa-solid fa-file-word text-3xl text-blue-900 mb-2"></i>
                            <p class="text-xs font-bold text-slate-700 mb-2">Opción A: Subir Archivo Word (.docx) o Texto (.txt)</p>
                            <input type="file" id="input-docx-parse" accept=".docx,.txt" class="hidden" onchange="autoExtraerArchivo(this)">
                            <button onclick="document.getElementById('input-docx-parse').click()" class="bg-blue-900 hover:bg-blue-800 text-white text-xs font-semibold px-4 py-2 rounded-lg transition shadow-sm">
                                Seleccionar Archivo
                            </button>
                        </div>
                        <div class="bg-slate-50 border border-slate-200 rounded-xl p-4">
                            <p class="text-xs font-bold text-slate-700 mb-1">Opción B: O pegar texto / cuerpo de correo recibido:</p>
                            <textarea id="raw-email-input" rows="3" placeholder="SOLICITUD DE COTIZACIÓN DE SERVICIO DE CALIBRACIÓN...
1. Datos del solicitante: Empresa, Contacto, RFC...
2. Instrumentos..." class="w-full text-xs p-2 border border-slate-300 rounded-lg bg-white mb-2"></textarea>
                            <button onclick="autoExtraerTexto()" class="w-full bg-slate-200 hover:bg-slate-300 text-slate-800 font-semibold text-xs py-1.5 rounded-lg transition">
                                ✨ Auto-extraer desde Texto Pegado
                            </button>
                        </div>
                    </div>
                    <div id="parse-status" class="mt-3 text-xs font-semibold"></div>
                </div>

                <!-- Sección 1.2 Formulario Interactivo de Revisión y Asignación SSI -->
                <div class="bg-white rounded-xl shadow-sm border border-slate-200 p-6 space-y-6">
                    <div>
                        <h3 class="text-base font-bold text-slate-900 mb-1">1. Datos del Solicitante</h3>
                        <p class="text-xs text-slate-500 mb-3">Revise y ajuste los datos fiscales y de contacto del cliente antes del turnado.</p>
                        <div class="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs">
                            <div>
                                <label class="block font-bold text-slate-700 mb-1">Razón Social / Nombre del Cliente *</label>
                                <input type="text" id="cli-nombre" placeholder="Nombre de la empresa o persona..." class="w-full border border-slate-300 rounded-lg p-2 font-medium">
                            </div>
                            <div>
                                <label class="block font-bold text-slate-700 mb-1">Representante / Contacto</label>
                                <input type="text" id="cli-rep" placeholder="Nombre de contacto..." class="w-full border border-slate-300 rounded-lg p-2 font-medium">
                            </div>
                            <div>
                                <label class="block font-bold text-slate-700 mb-1">RFC</label>
                                <input type="text" id="cli-rfc" placeholder="RFC del cliente..." class="w-full border border-slate-300 rounded-lg p-2 font-medium">
                            </div>
                            <div>
                                <label class="block font-bold text-slate-700 mb-1">Correo Electrónico *</label>
                                <input type="email" id="cli-correo" placeholder="correo@empresa.com" class="w-full border border-slate-300 rounded-lg p-2 font-medium">
                            </div>
                            <div>
                                <label class="block font-bold text-slate-700 mb-1">Teléfono</label>
                                <input type="text" id="cli-tel" placeholder="Teléfono con lada..." class="w-full border border-slate-300 rounded-lg p-2 font-medium">
                            </div>
                            <div>
                                <label class="block font-bold text-slate-700 mb-1">País de Solicitud *</label>
                                <input type="text" id="cli-pais" value="México" onchange="verificarPaisCliente(this.value)" class="w-full border border-slate-300 rounded-lg p-2 font-medium">
                            </div>
                        </div>
                        <div class="mt-3 flex items-center space-x-2">
                            <input type="checkbox" id="cli-iva" checked class="rounded text-blue-900 w-4 h-4">
                            <label for="cli-iva" class="text-xs font-semibold text-slate-700">Aplica IVA general del 16% (Exentar si es cliente extranjero sin aprovechamiento en territorio nacional)</label>
                        </div>
                    </div>

                    <div class="border-t border-slate-200 pt-4">
                        <div class="flex justify-between items-center mb-2">
                            <div>
                                <h3 class="text-base font-bold text-slate-900">2. Consecutivos Institucionales y Modalidad del Expediente</h3>
                                <p class="text-xs text-slate-500">Regla Oficial CENAM: <strong>1 Folio Maestro ➔ N Solicitudes Independientes</strong>.</p>
                            </div>
                            <span class="bg-blue-100 text-blue-900 font-bold px-3 py-1 rounded-lg text-sm" id="display-folio">Folio: 0001-2026PR</span>
                        </div>
                    </div>

                    <div class="border-t border-slate-200 pt-4">
                        <div class="flex justify-between items-center mb-3">
                            <div>
                                <h3 class="text-base font-bold text-slate-900">3. Instrumentos a Calibrar y Clasificación por Área Técnica</h3>
                                <p class="text-xs text-slate-500">SSI determina a qué Área Técnica / División turnar cada equipo y si se realizará IN SITU con viáticos.</p>
                            </div>
                            <button onclick="agregarFilaInstrumento()" class="bg-slate-200 hover:bg-slate-300 text-slate-800 text-xs font-bold px-3 py-1.5 rounded-lg transition flex items-center gap-1.5">
                                <i class="fa-solid fa-plus"></i> Agregar Instrumento
                            </button>
                        </div>

                        <div id="instrumentos-list" class="space-y-4">
                            <!-- Filas dinámicas de instrumentos -->
                        </div>
                    </div>

                    <!-- Previsualización Dinámica de Solicitudes a Generar -->
                    <div class="border-t border-slate-200 pt-4">
                        <h4 class="text-xs font-bold text-slate-700 mb-2 flex items-center gap-1.5">
                            <i class="fa-solid fa-diagram-project text-blue-900"></i> Previsualización de Solicitudes a Generar por Área y Modalidad (Alternativa 3):
                        </h4>
                        <div id="previsualizacion-solicitudes" class="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs">
                            <div class="p-3 bg-slate-50 rounded-lg border border-slate-200 text-slate-500 italic">No hay instrumentos clasificados aún.</div>
                        </div>
                    </div>

                    <!-- Botón Final de Turnado -->
                    <div class="border-t border-slate-200 pt-4 flex justify-end">
                        <button onclick="registrarExpedienteOficial()" class="bg-blue-900 hover:bg-blue-800 text-white font-bold text-xs px-6 py-3 rounded-xl transition shadow-md flex items-center gap-2">
                            <i class="fa-solid fa-paper-plane"></i> Registrar Expediente y Turnar Solicitudes a ATs
                        </button>
                    </div>
                </div>
            </div>

            <!-- SSI PESTAÑA 2: SOLICITUDES DEVUELTAS POR AT -->
            <div id="ssi-panel-2" class="space-y-4 hidden">
                <div class="flex justify-between items-center mb-2">
                    <div>
                        <h2 class="text-lg font-bold text-slate-900">Bandeja de Solicitudes Devueltas por Áreas Técnicas</h2>
                        <p class="text-xs text-slate-500">Solicitudes que las Áreas Técnicas determinaron que no corresponden a su alcance metrológico y requieren reasignación.</p>
                    </div>
                    <button onclick="loadDevueltasSSI()" class="text-xs bg-slate-200 hover:bg-slate-300 text-slate-700 px-3 py-1.5 rounded-md font-semibold">
                        <i class="fa-solid fa-arrows-rotate"></i> Actualizar
                    </button>
                </div>
                <div id="devueltas-container" class="space-y-3">
                    <div class="text-center py-8 text-slate-500">Consultando solicitudes devueltas...</div>
                </div>
            </div>

            <!-- SSI PESTAÑA 3: EMISIÓN DE COTIZACIÓN -->
            <div id="ssi-panel-3" class="space-y-4 hidden">
                <div class="flex justify-between items-center mb-2">
                    <div>
                        <h2 class="text-lg font-bold text-slate-900">Consolidación y Emisión de Cotizaciones Oficiales</h2>
                        <p class="text-xs text-slate-500">Cálculo contable exacto con IVA del 16%, auto-reparación preventiva y calidad estricta sin precios en $0.00.</p>
                    </div>
                    <div class="flex items-center space-x-2">
                        <select id="filtro-modo-cotiz" onchange="loadCotizacionesSSI()" class="text-xs bg-white border border-slate-300 rounded-lg p-1.5 font-semibold">
                            <option value="solicitud">Modo por Solicitud</option>
                            <option value="folio">Vista Integral por Folio (1 Folio ➔ N Solicitudes)</option>
                        </select>
                        <button onclick="loadCotizacionesSSI()" class="text-xs bg-slate-200 hover:bg-slate-300 text-slate-700 px-3 py-1.5 rounded-md font-semibold">
                            <i class="fa-solid fa-arrows-rotate"></i> Actualizar
                        </button>
                    </div>
                </div>
                <div id="cotizaciones-ssi-container" class="space-y-4">
                    <div class="text-center py-8 text-slate-500">Cargando cotizaciones...</div>
                </div>
            </div>

            <!-- SSI PESTAÑA 4: ACEPTACIÓN Y PROGRAMACIÓN -->
            <div id="ssi-panel-4" class="space-y-4 hidden">
                <div class="flex justify-between items-center mb-2">
                    <div>
                        <h2 class="text-lg font-bold text-slate-900">Aceptación de Partidas y Programación de Fechas</h2>
                        <p class="text-xs text-slate-500">Fase A: Capture la Orden de Compra/Oficio del cliente y partidas aprobadas. Fase B: Revise y apruebe las fechas programadas por las ATs.</p>
                    </div>
                    <button onclick="loadProgramacionSSI()" class="text-xs bg-slate-200 hover:bg-slate-300 text-slate-700 px-3 py-1.5 rounded-md font-semibold">
                        <i class="fa-solid fa-arrows-rotate"></i> Actualizar
                    </button>
                </div>
                <div id="programacion-ssi-container" class="space-y-4">
                    <div class="text-center py-8 text-slate-500">Cargando programación...</div>
                </div>
            </div>

            <!-- SSI PESTAÑA 5: CONTRATOS Y CONFIRMACIÓN -->
            <div id="ssi-panel-5" class="space-y-4 hidden">
                <div class="flex justify-between items-center mb-2">
                    <div>
                        <h2 class="text-lg font-bold text-slate-900">Formalización de Contratos y Reserva de Laboratorio</h2>
                        <p class="text-xs text-slate-500">Descargue el Contrato Oficial (Carta) y confirme la reserva con los laboratorios técnicos.</p>
                    </div>
                    <button onclick="loadConfirmacionSSI()" class="text-xs bg-slate-200 hover:bg-slate-300 text-slate-700 px-3 py-1.5 rounded-md font-semibold">
                        <i class="fa-solid fa-arrows-rotate"></i> Actualizar
                    </button>
                </div>
                <div id="confirmacion-ssi-container" class="space-y-4">
                    <div class="text-center py-8 text-slate-500">Cargando contratos...</div>
                </div>
            </div>

            <!-- SSI PESTAÑA 6: MANTENIMIENTO -->
            <div id="ssi-panel-6" class="space-y-6 hidden">
                <div class="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
                    <h2 class="text-lg font-bold text-red-700 mb-2 flex items-center gap-2">
                        <i class="fa-solid fa-triangle-exclamation"></i> Zona de Mantenimiento y Reinicio Operativo
                    </h2>
                    <p class="text-sm text-slate-600 mb-4">
                        Permite reiniciar el sistema a estado cero eliminando solicitudes de prueba y reiniciando el consecutivo a <strong>0001-2026PR</strong>. Los <strong>1,036 servicios</strong>, <strong>294 laboratorios</strong> y <strong>15 divisiones técnicas</strong> permanecen 100% protegidos e intactos.
                    </p>
                    <button onclick="limpiarBaseDatos()" class="bg-red-700 hover:bg-red-800 text-white font-semibold text-xs px-4 py-2.5 rounded-lg transition flex items-center gap-2">
                        <i class="fa-solid fa-broom"></i> Ejecutar Limpieza a Estado Cero
                    </button>
                    <div id="maint-status" class="mt-4"></div>
                </div>
            </div>
        </div>

        <!-- ============================================== -->
        <!-- VISTA DE ÁREA TÉCNICA (CS-AT) -->
        <!-- ============================================== -->
        <div id="view-at" class="hidden space-y-6">
            <!-- Barra Superior de Área Técnica -->
            <div class="bg-white p-4 rounded-xl shadow-sm border border-slate-200 flex flex-wrap items-center justify-between gap-4">
                <div class="flex items-center space-x-3">
                    <span class="text-sm font-bold text-slate-700">División Técnica Oficial:</span>
                    <div id="at-area-selector-wrapper" class="flex items-center">
                        <select id="select-area-at" onchange="changeAreaAT(this.value)" class="text-sm bg-slate-50 border border-slate-300 rounded-lg px-3 py-1.5 font-semibold text-slate-800 focus:ring-2 focus:ring-blue-900">
                        <option value="740">740 - Dirección de Metrología Dimensional</option>
                        <option value="730">730 - Dirección de Masa y Densidad</option>
                        <option value="720">720 - Dirección de Fuerza y Presión</option>
                        <option value="710">710 - Dirección de Flujo y Volumen</option>
                        <option value="410">410 - Dirección de Mediciones Electromagnéticas</option>
                        <option value="420">420 - Dirección de Termometría</option>
                        <option value="430">430 - Dirección de Tiempo y Frecuencia</option>
                        <option value="440">440 - Dirección de Radiofrecuencias</option>
                        <option value="510">510 - Dirección de Vibraciones y Acústica</option>
                        <option value="520">520 - Dirección de Óptica y Radiometría</option>
                        <option value="610">610 - Dirección de Materiales Metálicos y Cerámicos</option>
                        <option value="620">620 - Dirección de Materiales Inorgánicos</option>
                        <option value="630">630 - Dirección de Materiales Orgánicos</option>
                        <option value="700">700 - Dirección de Metrología Mecánica</option>
                        <option value="810">810 - Dirección de Servicios Tecnológicos</option>
                    </select>
                    <!-- Indicador bloqueado cuando ingresa un especialista de área técnica -->
                    <span id="at-area-locked-badge" class="hidden text-sm font-extrabold text-blue-900 bg-blue-50 border border-blue-200 px-3 py-1.5 rounded-lg flex items-center">
                        <i class="fa-solid fa-lock text-blue-700 mr-2"></i> <span id="at-area-locked-name">Área Asignada</span>
                    </span>
                    </div>
                </div>
                <div class="flex space-x-2">
                    <button onclick="setTabAT(1)" id="at-tab-1" class="px-3 py-1.5 rounded-lg text-xs font-semibold bg-blue-900 text-white">
                        <i class="fa-solid fa-microscope mr-1"></i> 1. Cotización Metrológica
                    </button>
                    <button onclick="setTabAT(2)" id="at-tab-2" class="px-3 py-1.5 rounded-lg text-xs font-semibold text-slate-600 bg-slate-100 hover:bg-slate-200">
                        <i class="fa-solid fa-calendar mr-1"></i> 2. Programación de Fechas
                    </button>
                    <button onclick="setTabAT(3)" id="at-tab-3" class="px-3 py-1.5 rounded-lg text-xs font-semibold text-slate-600 bg-slate-100 hover:bg-slate-200">
                        <i class="fa-solid fa-calendar-check mr-1"></i> 3. Calendario Confirmado
                    </button>
                </div>
            </div>

            <!-- AT PESTAÑA 1: COTIZACIÓN METROLÓGICA -->
            <div id="at-panel-1" class="space-y-4">
                <div id="at-cotizaciones-container" class="space-y-4">
                    <div class="text-center py-8 text-slate-500">Cargando solicitudes para el área seleccionada...</div>
                </div>
            </div>

            <!-- AT PESTAÑA 2: PROGRAMACIÓN DE FECHAS -->
            <div id="at-panel-2" class="space-y-4 hidden">
                <div id="at-programacion-container" class="space-y-4">
                    <div class="text-center py-8 text-slate-500">Cargando solicitudes para programar fechas...</div>
                </div>
            </div>

            <!-- AT PESTAÑA 3: CALENDARIO CONFIRMADO -->
            <div id="at-panel-3" class="space-y-4 hidden">
                <div class="flex justify-between items-center mb-2">
                    <div>
                        <h3 class="text-base font-bold text-slate-900">Servicios Confirmados y Reservas en Laboratorio</h3>
                        <p class="text-xs text-slate-500">Consulta operativa de fechas confirmadas para el resguardo y disponibilidad de patrones y personal.</p>
                    </div>
                    <button onclick="loadCalendarioAT()" class="text-xs bg-slate-200 hover:bg-slate-300 text-slate-700 px-3 py-1.5 rounded-md font-semibold">
                        <i class="fa-solid fa-arrows-rotate"></i> Actualizar
                    </button>
                </div>
                <div id="at-calendario-container" class="space-y-4">
                    <div class="text-center py-8 text-slate-500">Cargando calendario confirmado...</div>
                </div>
            </div>
        </div>


    <!-- ============================================== -->
    <!-- MODAL DE INICIO DE SESIÓN INSTITUCIONAL CENAM  -->
    <!-- ============================================== -->
    <div id="modal-login" class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/70 backdrop-blur-sm hidden">
        <div class="bg-white rounded-2xl shadow-2xl border border-slate-200 max-w-lg w-full mx-4 p-6 overflow-hidden">
            <div class="text-center mb-6">
                <img src="/static/cenam_logo.png" alt="CENAM" class="h-16 mx-auto mb-3 object-contain" onerror="this.src='/static/img/logo_cenam.png'">
                <h2 class="text-xl font-extrabold text-slate-900">Control de Acceso Institucional</h2>
                <p class="text-xs text-slate-500 mt-1">Inicie sesión con su usuario para acceder exclusivamente a sus solicitudes</p>
            </div>

            <!-- Selector Rápido de Cuenta Institucional -->
            <div class="mb-4">
                <label class="block text-xs font-bold text-slate-700 mb-1.5">
                    <i class="fa-solid fa-id-card-clip text-blue-900 mr-1"></i> Seleccione Perfil / Área Técnica:
                </label>
                <select id="login-quick-select" onchange="seleccionarCuentaRapida(this.value)" class="w-full bg-slate-50 border border-slate-300 rounded-lg p-2.5 text-xs font-bold text-slate-800 focus:ring-2 focus:ring-blue-900">
                    <option value="">-- Seleccionar Área o Ventanilla --</option>
                    <optgroup label="Ventanilla Central y Gestión">
                        <option value="ssi@cenam.mx">🏢 Ventanilla Central SSI (ssi@cenam.mx)</option>
                        <option value="admin@cenam.mx">🔑 Administrador General (admin@cenam.mx)</option>
                    </optgroup>
                    <optgroup label="Divisiones Técnicas Oficiales (15 Áreas AT)">
                        <option value="at740@cenam.mx">🔬 740 - Dirección de Metrología Dimensional</option>
                        <option value="at730@cenam.mx">⚖️ 730 - Dirección de Masa y Densidad</option>
                        <option value="at720@cenam.mx">⚡ 720 - Dirección de Fuerza y Presión</option>
                        <option value="at710@cenam.mx">💧 710 - Dirección de Flujo y Volumen</option>
                        <option value="at700@cenam.mx">⚙️ 700 - Dirección de Metrología Mecánica</option>
                        <option value="at410@cenam.mx">⚡ 410 - Dirección de Mediciones Electromagnéticas</option>
                        <option value="at420@cenam.mx">🌡️ 420 - Dirección de Termometría</option>
                        <option value="at430@cenam.mx">⏱️ 430 - Dirección de Tiempo y Frecuencia</option>
                        <option value="at440@cenam.mx">📡 440 - Dirección de Radiofrecuencias</option>
                        <option value="at510@cenam.mx">🔊 510 - Dirección de Vibraciones y Acústica</option>
                        <option value="at520@cenam.mx">💡 520 - Dirección de Óptica y Radiometría</option>
                        <option value="at610@cenam.mx">🔩 610 - Dirección de Materiales Metálicos y Cerámicos</option>
                        <option value="at620@cenam.mx">🧪 620 - Dirección de Materiales Inorgánicos</option>
                        <option value="at630@cenam.mx">🧬 630 - Dirección de Materiales Orgánicos</option>
                        <option value="at810@cenam.mx">🏢 810 - Dirección de Servicios Tecnológicos</option>
                    </optgroup>
                </select>
            </div>

            <!-- Formulario de Credenciales -->
            <form id="form-login" onsubmit="ejecutarLogin(event)" class="space-y-3">
                <div>
                    <label class="block text-xs font-semibold text-slate-600 mb-1">Correo Institucional:</label>
                    <input type="email" id="login-correo" required placeholder="ejemplo@cenam.mx" class="w-full bg-white border border-slate-300 rounded-lg p-2.5 text-xs text-slate-800 font-medium">
                </div>
                <div>
                    <label class="block text-xs font-semibold text-slate-600 mb-1">Contraseña:</label>
                    <input type="password" id="login-pwd" required value="Cenam2026*" placeholder="••••••••" class="w-full bg-white border border-slate-300 rounded-lg p-2.5 text-xs text-slate-800">
                </div>
                <div id="login-error-msg" class="text-xs text-red-600 font-semibold hidden"></div>
                <button type="submit" class="w-full bg-blue-900 hover:bg-blue-800 text-white font-bold py-2.5 rounded-lg text-xs shadow-md transition flex items-center justify-center gap-2 mt-2">
                    <i class="fa-solid fa-right-to-bracket"></i> Iniciar Sesión Segura
                </button>
            </form>
        </div>
    </div>

    </main>

    <footer class="mt-12 py-6 text-center text-xs text-slate-500 border-t border-slate-200">
        Centro Nacional de Metrología (CENAM) &bull; Servidor Uvicorn ASGI de Alto Rendimiento &bull; ISO/IEC 17025
    </footer>

    <!-- Scripts de la Aplicación -->
    <script>
        let currentUser = null;
        let currentRole = 'SSI';
        let currentAreaAT = '740';
        let catalogoAreas = [];
        let allServicesCache = {};
        let allLabsCache = {};
        let instrumentosState = [];

        const DIVISIONES_OFICIALES = [
            { clave: '740', nombre: '740 - Dirección de Metrología Dimensional' },
            { clave: '730', nombre: '730 - Dirección de Masa y Densidad' },
            { clave: '720', nombre: '720 - Dirección de Fuerza y Presión' },
            { clave: '710', nombre: '710 - Dirección de Flujo y Volumen' },
            { clave: '410', nombre: '410 - Dirección de Mediciones Electromagnéticas' },
            { clave: '420', nombre: '420 - Dirección de Termometría' },
            { clave: '430', nombre: '430 - Dirección de Tiempo y Frecuencia' },
            { clave: '440', nombre: '440 - Dirección de Radiofrecuencias' },
            { clave: '510', nombre: '510 - Dirección de Vibraciones y Acústica' },
            { clave: '520', nombre: '520 - Dirección de Óptica y Radiometría' },
            { clave: '610', nombre: '610 - Dirección de Materiales Metálicos y Cerámicos' },
            { clave: '620', nombre: '620 - Dirección de Materiales Inorgánicos' },
            { clave: '630', nombre: '630 - Dirección de Materiales Orgánicos' },
            { clave: '700', nombre: '700 - Dirección de Metrología Mecánica' },
            { clave: '810', nombre: '810 - Dirección de Servicios Tecnológicos' }
        ];

        // Inicialización al cargar la página con autenticación
        window.addEventListener('DOMContentLoaded', () => {
            inicializarFormularioVacio();
            verificarSesionUsuario();
        });

        // ==============================================
        // GESTIÓN DE SESIÓN Y CONTROL DE ACCESO
        // ==============================================

        function verificarSesionUsuario() {
            const stored = localStorage.getItem('cenam_user');
            if (stored) {
                try {
                    currentUser = JSON.parse(stored);
                    aplicarPerfilUsuario(currentUser);
                    return;
                } catch (e) {
                    localStorage.removeItem('cenam_user');
                }
            }
            abrirModalLogin();
        }

        function abrirModalLogin() {
            document.getElementById('modal-login').classList.remove('hidden');
        }

        function seleccionarCuentaRapida(correo) {
            if (!correo) return;
            document.getElementById('login-correo').value = correo;
            document.getElementById('login-pwd').value = 'Cenam2026*';
            document.getElementById('login-error-msg').classList.add('hidden');
        }

        async function ejecutarLogin(e) {
            e.preventDefault();
            const correo = document.getElementById('login-correo').value.trim();
            const password = document.getElementById('login-pwd').value.trim();
            const errorDiv = document.getElementById('login-error-msg');
            errorDiv.classList.add('hidden');

            try {
                const res = await fetch('/api/auth/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ correo, password })
                });
                let data = null;
                const contentType = res.headers.get("content-type") || "";
                if (contentType.includes("application/json")) {
                    data = await res.json();
                } else {
                    const text = await res.text();
                    data = { detail: text || `Error del servidor (${res.status})` };
                }
                if (!res.ok || data.status !== 'success') {
                    errorDiv.innerText = data.detail || 'Credenciales inválidas. Verifique correo y contraseña.';
                    errorDiv.classList.remove('hidden');
                    return;
                }

                currentUser = data.user;
                localStorage.setItem('cenam_user', JSON.stringify(currentUser));
                document.getElementById('modal-login').classList.add('hidden');
                aplicarPerfilUsuario(currentUser);
            } catch (err) {
                errorDiv.innerText = 'Error de conexión con el servidor.';
                errorDiv.classList.remove('hidden');
            }
        }

        function cerrarSesion() {
            localStorage.removeItem('cenam_user');
            currentUser = null;
            abrirModalLogin();
        }

        function aplicarPerfilUsuario(user) {
            // Actualizar badge en barra superior
            const nameDisp = document.getElementById('user-name-display');
            if (nameDisp) {
                nameDisp.innerText = `${user.nombre_completo}`;
            }

            const btnSSI = document.getElementById('btn-role-ssi');
            const btnAT = document.getElementById('btn-role-at');
            const selectArea = document.getElementById('select-area-at');
            const lockedBadge = document.getElementById('at-area-locked-badge');
            const lockedName = document.getElementById('at-area-locked-name');

            if (user.rol === 'AT') {
                // Usuario restringido exclusivamente a su Área Técnica
                currentAreaAT = user.clave_area || '740';
                
                // Ocultar botón de SSI
                if (btnSSI) btnSSI.classList.add('hidden');
                if (btnAT) btnAT.classList.remove('hidden');

                // Bloquear selector de área para que no acceda a otras divisiones
                if (selectArea) {
                    selectArea.value = currentAreaAT;
                    selectArea.classList.add('hidden');
                }
                if (lockedBadge) {
                    lockedBadge.classList.remove('hidden');
                    const divInfo = DIVISIONES_OFICIALES.find(d => d.clave === currentAreaAT);
                    lockedName.innerText = divInfo ? divInfo.nombre : `Área ${currentAreaAT}`;
                }

                // Cambiar a vista de AT automáticamente
                setRole('AT');
            } else if (user.rol === 'SSI') {
                // Usuario de Ventanilla Central SSI
                if (btnSSI) btnSSI.classList.remove('hidden');
                if (btnAT) btnAT.classList.add('hidden');
                setRole('SSI');
            } else {
                // Administrador: acceso total
                if (btnSSI) btnSSI.classList.remove('hidden');
                if (btnAT) btnAT.classList.remove('hidden');
                if (selectArea) selectArea.classList.remove('hidden');
                if (lockedBadge) lockedBadge.classList.add('hidden');
                setRole('SSI');
            }
        }

        async function actualizarContadoresSSI() {
            try {
                const res = await fetch('/api/ssi/resumen-contadores');
                if (res.ok) {
                    const d = await res.json();
                    document.getElementById('badge-devueltas').innerText = d.devueltas || 0;
                    document.getElementById('badge-cotiz').innerText = d.cotiz_listas || 0;
                    document.getElementById('badge-prog').innerText = d.en_programacion || 0;
                }
            } catch (e) {}
        }

        function setRole(role) {
            if (currentUser && currentUser.rol === 'AT' && role === 'SSI') {
                alert("Acceso Restringido: Su cuenta técnica (" + currentUser.correo + ") está asignada exclusivamente a la División " + currentUser.clave_area + ".");
                return;
            }

            currentRole = role;
            if (role === 'SSI') {
                document.getElementById('view-ssi').classList.remove('hidden');
                document.getElementById('view-at').classList.add('hidden');
                document.getElementById('btn-role-ssi').className = "px-3 py-1.5 rounded-md text-xs font-semibold bg-blue-900 text-white shadow-sm flex items-center gap-1.5 transition";
                document.getElementById('btn-role-at').className = "px-3 py-1.5 rounded-md text-xs font-semibold text-slate-600 hover:text-slate-900 flex items-center gap-1.5 transition";
                actualizarContadoresSSI();
            } else {
                document.getElementById('view-ssi').classList.add('hidden');
                document.getElementById('view-at').classList.remove('hidden');
                document.getElementById('btn-role-ssi').className = "px-3 py-1.5 rounded-md text-xs font-semibold text-slate-600 hover:text-slate-900 flex items-center gap-1.5 transition";
                document.getElementById('btn-role-at').className = "px-3 py-1.5 rounded-md text-xs font-semibold bg-blue-900 text-white shadow-sm flex items-center gap-1.5 transition";
                loadPendingAT();
            }
        }

        function setTabSSI(tab) {
            for (let i = 1; i <= 6; i++) {
                document.getElementById(`ssi-panel-${i}`).classList.add('hidden');
                document.getElementById(`ssi-tab-${i}`).className = "px-4 py-2 text-sm font-semibold border-b-2 border-transparent text-slate-600 hover:text-slate-900 flex items-center gap-2";
            }
            document.getElementById(`ssi-panel-${tab}`).classList.remove('hidden');
            document.getElementById(`ssi-tab-${tab}`).className = "px-4 py-2 text-sm font-semibold border-b-2 border-blue-900 text-blue-900 flex items-center gap-2";

            if (tab === 2) loadDevueltasSSI();
            if (tab === 3) loadCotizacionesSSI();
            if (tab === 4) loadProgramacionSSI();
            if (tab === 5) loadConfirmacionSSI();
        }

        function setTabAT(tab) {
            document.getElementById('at-panel-1').classList.toggle('hidden', tab !== 1);
            document.getElementById('at-panel-2').classList.toggle('hidden', tab !== 2);
            document.getElementById('at-panel-3').classList.toggle('hidden', tab !== 3);
            document.getElementById('at-tab-1').className = tab === 1 ? "px-3 py-1.5 rounded-lg text-xs font-semibold bg-blue-900 text-white" : "px-3 py-1.5 rounded-lg text-xs font-semibold text-slate-600 bg-slate-100 hover:bg-slate-200";
            document.getElementById('at-tab-2').className = tab === 2 ? "px-3 py-1.5 rounded-lg text-xs font-semibold bg-blue-900 text-white" : "px-3 py-1.5 rounded-lg text-xs font-semibold text-slate-600 bg-slate-100 hover:bg-slate-200";
            document.getElementById('at-tab-3').className = tab === 3 ? "px-3 py-1.5 rounded-lg text-xs font-semibold bg-blue-900 text-white" : "px-3 py-1.5 rounded-lg text-xs font-semibold text-slate-600 bg-slate-100 hover:bg-slate-200";
            if (tab === 1) loadPendingAT();
            if (tab === 2) loadProgramacionAT();
            if (tab === 3) loadCalendarioAT();
        }

        function changeAreaAT(area) {
            currentAreaAT = area;
            loadPendingAT();
        }

        // ========================================================
        // SSI PASO 1: EXTRACCIÓN Y REVISIÓN INTERACTIVA
        // ========================================================

        async function inicializarFormularioVacio() {
            try {
                const res = await fetch('/api/solicitudes/siguiente-folio');
                const d = await res.json();
                document.getElementById('display-folio').innerText = `Folio: ${d.no_folio}`;
            } catch (e) {}

            instrumentosState = [
                {
                    numero: 1,
                    desc: "Detector de fugas acústico",
                    marca: "Mesa Engineering",
                    modelo: "2D",
                    serie: "SN-1001",
                    id_interno: "PR-EQ-01",
                    alcance: "<= 80 kHz",
                    magnitud: "Vibraciones y Acústica",
                    certificado_anterior: "",
                    condiciones: "",
                    clave_area: "510",
                    es_in_situ: 0
                },
                {
                    numero: 2,
                    desc: "Multímetro digital 6.5 dígitos",
                    marca: "Fluke",
                    modelo: "8846A",
                    serie: "SN-1002",
                    id_interno: "PR-EQ-02",
                    alcance: "100 mV a 1000 V",
                    magnitud: "Eléctrica",
                    certificado_anterior: "",
                    condiciones: "",
                    clave_area: "410",
                    es_in_situ: 0
                }
            ];
            renderInstrumentosForm();
        }

        async function autoExtraerArchivo(input) {
            if (!input.files || input.files.length === 0) return;
            const file = input.files[0];
            const statusDiv = document.getElementById('parse-status');
            statusDiv.innerHTML = `<span class="text-blue-700"><i class="fa-solid fa-spinner fa-spin"></i> Extrayendo datos de "${file.name}"...</span>`;
            
            const formData = new FormData();
            formData.append('file', file);

            try {
                const res = await fetch('/api/solicitudes/extraer-datos', {
                    method: 'POST',
                    body: formData
                });
                let data = null;
                const contentType = res.headers.get("content-type") || "";
                if (contentType.includes("application/json")) {
                    data = await res.json();
                } else {
                    const text = await res.text();
                    data = { detail: text || `Error del servidor (${res.status})` };
                }
                if (res.ok) {
                    cargarDatosExtraidosEnFormulario(data);
                    statusDiv.innerHTML = `<span class="text-emerald-700 font-bold"><i class="fa-solid fa-circle-check"></i> Datos extraídos exitosamente. Revise los campos abajo antes de turnar.</span>`;
                } else {
                    statusDiv.innerHTML = `<span class="text-red-700 font-bold">Error: ${data.detail || 'No se pudo procesar'}</span>`;
                }
            } catch (err) {
                statusDiv.innerHTML = `<span class="text-red-700 font-bold">Error de red: ${err.message}</span>`;
            }
        }

        async function autoExtraerTexto() {
            const rawText = document.getElementById('raw-email-input').value;
            const statusDiv = document.getElementById('parse-status');
            if (!rawText.trim()) {
                alert("Por favor pegue el texto o correo recibido antes de extraer.");
                return;
            }
            statusDiv.innerHTML = `<span class="text-blue-700"><i class="fa-solid fa-spinner fa-spin"></i> Extrayendo datos del texto...</span>`;

            const formData = new FormData();
            formData.append('raw_text', rawText);

            try {
                const res = await fetch('/api/solicitudes/extraer-datos', {
                    method: 'POST',
                    body: formData
                });
                let data = null;
                const contentType = res.headers.get("content-type") || "";
                if (contentType.includes("application/json")) {
                    data = await res.json();
                } else {
                    const text = await res.text();
                    data = { detail: text || `Error del servidor (${res.status})` };
                }
                if (res.ok) {
                    cargarDatosExtraidosEnFormulario(data);
                    statusDiv.innerHTML = `<span class="text-emerald-700 font-bold"><i class="fa-solid fa-circle-check"></i> Datos extraídos exitosamente. Revise y asigne abajo.</span>`;
                } else {
                    statusDiv.innerHTML = `<span class="text-red-700 font-bold">Error: ${data.detail || 'No se pudo extraer'}</span>`;
                }
            } catch (err) {
                statusDiv.innerHTML = `<span class="text-red-700 font-bold">Error: ${err.message}</span>`;
            }
        }

        function cargarDatosExtraidosEnFormulario(data) {
            if (data.no_folio) {
                document.getElementById('display-folio').innerText = `Folio: ${data.no_folio}`;
            }
            if (data.cliente) {
                document.getElementById('cli-nombre').value = data.cliente.cliente || '';
                document.getElementById('cli-rep').value = data.cliente.representante || '';
                document.getElementById('cli-correo').value = data.cliente.correo || '';
                document.getElementById('cli-tel').value = data.cliente.telefono || '';
                document.getElementById('cli-rfc').value = data.cliente.rfc || '';
                document.getElementById('cli-pais').value = data.cliente.pais || 'México';
                document.getElementById('cli-iva').checked = data.cliente.aplica_iva !== 0;
            }
            if (data.instrumentos && data.instrumentos.length > 0) {
                instrumentosState = data.instrumentos;
            }
            renderInstrumentosForm();
        }

        function renderInstrumentosForm() {
            const container = document.getElementById('instrumentos-list');
            let html = '';

            instrumentosState.forEach((inst, idx) => {
                let optAreas = '';
                DIVISIONES_OFICIALES.forEach(div => {
                    const sel = (inst.clave_area === div.clave) ? 'selected' : '';
                    optAreas += `<option value="${div.clave}" ${sel}>${div.nombre}</option>`;
                });

                html += `
                <div class="border border-slate-200 rounded-xl p-4 bg-slate-50 text-xs shadow-sm" id="inst_card_${idx}">
                    <div class="flex justify-between items-center border-b border-slate-200 pb-2 mb-3">
                        <span class="font-bold text-slate-900 text-sm"><i class="fa-solid fa-screwdriver-wrench text-blue-900 mr-1.5"></i> Instrumento ${idx + 1}</span>
                        <button onclick="eliminarInstrumento(${idx})" class="text-red-600 hover:text-red-800 font-bold text-xs flex items-center gap-1">
                            <i class="fa-solid fa-trash"></i> Quitar
                        </button>
                    </div>
                    <div class="grid grid-cols-1 md:grid-cols-3 gap-3 mb-3">
                        <div class="md:col-span-2">
                            <label class="block font-bold text-slate-700 mb-1">Descripción del Instrumento *</label>
                            <input type="text" id="inst_desc_${idx}" value="${inst.desc || ''}" onchange="updateInstField(${idx}, 'desc', this.value)" class="w-full bg-white border border-slate-300 rounded-lg p-2 font-medium">
                        </div>
                        <div>
                            <label class="block font-bold text-slate-700 mb-1">Intervalo / Alcance Requerido</label>
                            <input type="text" id="inst_alc_${idx}" value="${inst.alcance || ''}" onchange="updateInstField(${idx}, 'alcance', this.value)" class="w-full bg-white border border-slate-300 rounded-lg p-2">
                        </div>
                    </div>
                    <div class="grid grid-cols-1 md:grid-cols-4 gap-3 mb-3">
                        <div>
                            <label class="block font-bold text-slate-700 mb-1">Marca</label>
                            <input type="text" id="inst_marca_${idx}" value="${inst.marca || ''}" onchange="updateInstField(${idx}, 'marca', this.value)" class="w-full bg-white border border-slate-300 rounded-lg p-2">
                        </div>
                        <div>
                            <label class="block font-bold text-slate-700 mb-1">Modelo</label>
                            <input type="text" id="inst_mod_${idx}" value="${inst.modelo || ''}" onchange="updateInstField(${idx}, 'modelo', this.value)" class="w-full bg-white border border-slate-300 rounded-lg p-2">
                        </div>
                        <div>
                            <label class="block font-bold text-slate-700 mb-1">No. Serie</label>
                            <input type="text" id="inst_ser_${idx}" value="${inst.serie || ''}" onchange="updateInstField(${idx}, 'serie', this.value)" class="w-full bg-white border border-slate-300 rounded-lg p-2">
                        </div>
                        <div>
                            <label class="block font-bold text-slate-700 mb-1">ID Interno</label>
                            <input type="text" id="inst_id_${idx}" value="${inst.id_interno || ''}" onchange="updateInstField(${idx}, 'id_interno', this.value)" class="w-full bg-white border border-slate-300 rounded-lg p-2">
                        </div>
                    </div>
                    <div class="grid grid-cols-1 md:grid-cols-3 gap-3 p-3 bg-white rounded-lg border border-slate-200">
                        <div class="md:col-span-2">
                            <label class="block font-bold text-blue-900 mb-1"><i class="fa-solid fa-arrows-split-up-and-left mr-1"></i> División Destino (Área Técnica asignada por SSI):</label>
                            <select id="inst_area_${idx}" onchange="updateInstField(${idx}, 'clave_area', this.value)" class="w-full bg-slate-50 border border-blue-900 text-blue-900 font-bold rounded-lg p-2">
                                ${optAreas}
                            </select>
                        </div>
                        <div class="flex items-center pt-5">
                            <label class="flex items-center space-x-2 cursor-pointer font-bold text-amber-900">
                                <input type="checkbox" id="inst_insitu_${idx}" ${inst.es_in_situ ? 'checked' : ''} onchange="updateInstField(${idx}, 'es_in_situ', this.checked ? 1 : 0)" class="rounded w-4 h-4 text-amber-700">
                                <span>🚗 IN SITU (En sitio con viáticos)</span>
                            </label>
                        </div>
                    </div>
                </div>
                `;
            });

            container.innerHTML = html;
            renderPrevisualizacionGrupos();
        }

        function updateInstField(index, field, value) {
            instrumentosState[index][field] = value;
            renderPrevisualizacionGrupos();
        }

        function agregarFilaInstrumento() {
            instrumentosState.push({
                numero: instrumentosState.length + 1,
                desc: "",
                marca: "",
                modelo: "",
                serie: "",
                id_interno: `PR-EQ-${String(instrumentosState.length + 1).padStart(2, '0')}`,
                alcance: "",
                magnitud: "",
                certificado_anterior: "",
                condiciones: "",
                clave_area: "740",
                es_in_situ: 0
            });
            renderInstrumentosForm();
        }

        function eliminarInstrumento(index) {
            if (instrumentosState.length <= 1) {
                alert("Debe mantener al menos un instrumento en la solicitud.");
                return;
            }
            instrumentosState.splice(index, 1);
            renderInstrumentosForm();
        }

        function renderPrevisualizacionGrupos() {
            const container = document.getElementById('previsualizacion-solicitudes');
            const grupos = {};

            instrumentosState.forEach(inst => {
                const area = inst.clave_area || '740';
                const mod = inst.es_in_situ ? '🚗 IN SITU (Viáticos)' : '🔬 LAB CENAM';
                const key = `${area}_${mod}`;
                if (!grupos[key]) {
                    grupos[key] = { area: area, mod: mod, count: 0 };
                }
                grupos[key].count++;
            });

            let html = '';
            for (let k in grupos) {
                const g = grupos[k];
                const areaObj = DIVISIONES_OFICIALES.find(d => d.clave === g.area) || { nombre: g.area };
                html += `
                <div class="p-3 bg-white rounded-lg border border-slate-300 shadow-sm">
                    <span class="font-bold text-blue-900 block">${areaObj.nombre}</span>
                    <span class="text-xs font-semibold px-2 py-0.5 rounded ${g.mod.includes('IN SITU') ? 'bg-amber-100 text-amber-800' : 'bg-blue-100 text-blue-800'} mt-1 inline-block">${g.mod}</span>
                    <span class="block text-slate-600 font-bold mt-1">${g.count} partida(s) asignadas</span>
                </div>
                `;
            }
            container.innerHTML = html;
        }

        async function registrarExpedienteOficial() {
            const cliente = document.getElementById('cli-nombre').value.trim();
            if (!cliente) {
                alert("Por favor ingrese la Razón Social / Nombre del Cliente.");
                document.getElementById('cli-nombre').focus();
                return;
            }

            for (let i = 0; i < instrumentosState.length; i++) {
                if (!instrumentosState[i].desc.trim()) {
                    alert(`Por favor ingrese la descripción para el Instrumento ${i + 1}.`);
                    return;
                }
            }

            const payload = {
                cliente: {
                    cliente: cliente,
                    representante: document.getElementById('cli-rep').value.trim(),
                    correo: document.getElementById('cli-correo').value.trim(),
                    telefono: document.getElementById('cli-tel').value.trim(),
                    rfc: document.getElementById('cli-rfc').value.trim(),
                    pais: document.getElementById('cli-pais').value.trim() || 'México',
                    aplica_iva: document.getElementById('cli-iva').checked ? 1 : 0
                },
                instrumentos: instrumentosState
            };

            try {
                const res = await fetch('/api/solicitudes/registrar-expediente', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                let data = null;
                const contentType = res.headers.get("content-type") || "";
                if (contentType.includes("application/json")) {
                    data = await res.json();
                } else {
                    const text = await res.text();
                    data = { detail: text || `Error del servidor (${res.status})` };
                }
                if (res.ok) {
                    const sols = data.data.solicitudes_creadas || [];
                    let solListStr = sols.map(s => `• Solicitud ${s.no_solicitud} (División ${s.clave_area} [${s.es_in_situ ? 'IN SITU' : 'LAB CENAM'}]) con ${s.total_partidas} partida(s)`).join('\\n');
                    alert(`🚀 ¡Expediente ${data.data.no_folio} Registrado con Éxito!\\n\\nSe generaron las siguientes solicitudes turnadas a las Áreas Técnicas:\\n${solListStr}`);
                    setTabSSI(3); // Pasar a cotizaciones
                    actualizarContadoresSSI();
                } else {
                    alert(`Error: ${data.detail || 'No se pudo registrar el expediente'}`);
                }
            } catch (err) {
                alert(`Error de red: ${err.message}`);
            }
        }

        // ========================================================
        // SSI PESTAÑA 2: SOLICITUDES DEVUELTAS
        // ========================================================

        async function loadDevueltasSSI() {
            const container = document.getElementById('devueltas-container');
            container.innerHTML = '<div class="text-center py-6 text-slate-500"><i class="fa-solid fa-spinner fa-spin"></i> Cargando solicitudes devueltas...</div>';
            try {
                const res = await fetch('/api/ssi/devueltas');
                const devueltas = await res.json();
                document.getElementById('badge-devueltas').innerText = devueltas.length;
                if (devueltas.length === 0) {
                    container.innerHTML = '<div class="bg-emerald-50 text-emerald-800 p-6 rounded-xl text-center font-medium">🎉 No hay solicitudes devueltas pendientes de reasignación. ¡Todo el flujo está en orden!</div>';
                    return;
                }

                let html = '';
                devueltas.forEach(d => {
                    let optAreas = '';
                    DIVISIONES_OFICIALES.forEach(div => {
                        const sel = (d.area_sugerida === div.clave) ? 'selected' : '';
                        optAreas += `<option value="${div.clave}" ${sel}>${div.nombre}</option>`;
                    });

                    html += `
                    <div class="bg-white rounded-xl shadow-sm border border-red-200 p-5">
                        <div class="flex justify-between items-start border-b border-slate-100 pb-3 mb-3">
                            <div>
                                <span class="bg-red-100 text-red-900 text-xs px-2.5 py-1 rounded font-bold">Folio: ${d.no_folio}</span>
                                <span class="bg-slate-100 text-slate-700 text-xs px-2.5 py-1 rounded font-bold ml-1">Solicitud: ${d.no_solicitud}</span>
                                <h3 class="text-base font-bold text-slate-900 mt-1">${d.cliente}</h3>
                            </div>
                            <span class="text-xs bg-red-100 text-red-800 font-bold px-2 py-1 rounded">Devuelta por CS-AT</span>
                        </div>
                        <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4 text-xs">
                            <div class="bg-slate-50 p-3 rounded-lg border border-slate-200">
                                <span class="font-bold text-slate-700 block mb-1">Área que devolvió: <strong class="text-red-700">${d.area_actual} - ${d.nombre_area_actual || ''}</strong></span>
                                <p class="text-slate-600 mb-2"><strong>Motivo técnico de devolución:</strong><br>${d.motivo_devolucion}</p>
                                ${d.area_sugerida ? `<span class="bg-amber-100 text-amber-800 px-2 py-0.5 rounded font-bold">💡 Área sugerida: ${d.area_sugerida} - ${d.nombre_area_sugerida || ''}</span>` : ''}
                            </div>
                            <div class="bg-blue-50 p-3 rounded-lg border border-blue-200 flex flex-col justify-between">
                                <div>
                                    <label class="block font-bold text-blue-900 mb-1">Reasignar a nueva Área Técnica Oficial:</label>
                                    <select id="reasig_sel_${d.sub_id}" class="w-full bg-white border border-slate-300 rounded-lg p-2 font-medium">
                                        ${optAreas}
                                    </select>
                                </div>
                                <button onclick="confirmarReasignacionSSI(${d.sub_id})" class="mt-3 bg-blue-900 hover:bg-blue-800 text-white font-bold py-2 px-4 rounded-lg text-xs transition">
                                    <i class="fa-solid fa-arrows-rotate mr-1"></i> Confirmar Reasignación
                                </button>
                            </div>
                        </div>
                    </div>
                    `;
                });
                container.innerHTML = html;
            } catch (err) {
                container.innerHTML = `<div class="text-red-700 text-xs">Error: ${err.message}</div>`;
            }
        }

        async function confirmarReasignacionSSI(subId) {
            const sel = document.getElementById(`reasig_sel_${subId}`);
            const nuevaArea = sel.value;
            try {
                const res = await fetch('/api/ssi/reasignar-solicitud', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ sub_solicitud_id: subId, nueva_area: nuevaArea })
                });
                let data = null;
                const contentType = res.headers.get("content-type") || "";
                if (contentType.includes("application/json")) {
                    data = await res.json();
                } else {
                    const text = await res.text();
                    data = { detail: text || `Error del servidor (${res.status})` };
                }
                if (res.ok) {
                    alert(data.message);
                    loadDevueltasSSI();
                    actualizarContadoresSSI();
                } else {
                    alert("Error: " + (data.detail || "No se pudo reasignar"));
                }
            } catch (err) {
                alert(`Error de red: ${err.message}`);
            }
        }

        // ========================================================
        // SSI PESTAÑA 3: EMISIÓN DE COTIZACIÓN
        // ========================================================

        async function loadCotizacionesSSI() {
            const container = document.getElementById('cotizaciones-ssi-container');
            container.innerHTML = '<div class="text-center py-6 text-slate-500"><i class="fa-solid fa-spinner fa-spin"></i> Cargando cotizaciones...</div>';
            try {
                const res = await fetch('/api/ssi/cotizaciones-pendientes');
                const cotizaciones = await res.json();
                document.getElementById('badge-cotiz').innerText = cotizaciones.length;
                if (cotizaciones.length === 0) {
                    container.innerHTML = '<div class="bg-emerald-50 text-emerald-800 p-6 rounded-xl text-center font-medium">🎉 No hay cotizaciones pendientes de emitir.</div>';
                    return;
                }
                let html = '';
                cotizaciones.forEach(s => {
                    const cerosAlert = s.tiene_ceros ? `
                        <div class="bg-red-50 border-l-4 border-red-500 p-3 mb-4 rounded text-xs text-red-800 font-medium">
                            <i class="fa-solid fa-triangle-exclamation mr-1"></i> <strong>Atención SSI:</strong> Existen ${s.partidas_ceros_count} partida(s) con costo $0.00. No es posible asignar No. de Cotización hasta asignar precios válidos.
                        </div>
                    ` : '';

                    let tableRows = '';
                    s.partidas.forEach(p => {
                        const pUnit = parseFloat(p.precio_unitario || 0.0);
                        const pTot = parseFloat(p.precio_total || 0.0);
                        const cant = parseInt(p.cantidad || 1);
                        const isCero = p.es_no_realizable === 0 && pUnit <= 0.0;
                        const rowBg = isCero ? 'bg-red-50' : '';
                        
                        tableRows += `
                            <tr class="${rowBg} border-b border-slate-100 text-xs">
                                <td class="py-2.5 px-3 font-bold">${p.numero_partida}</td>
                                <td class="py-2.5 px-3 font-semibold text-slate-800">${p.descripcion_equipo}</td>
                                <td class="py-2.5 px-3 text-slate-600">${p.descripcion_servicio || 'Pendiente'}</td>
                                <td class="py-2.5 px-3 text-center font-bold">${cant}</td>
                                <td class="py-2.5 px-3 text-right font-semibold ${isCero ? 'text-red-700 font-bold' : ''}">$${pUnit.toLocaleString('en-US', {minimumFractionDigits: 2})}</td>
                                <td class="py-2.5 px-3 text-right font-bold text-slate-900">$${pTot.toLocaleString('en-US', {minimumFractionDigits: 2})}</td>
                                <td class="py-2.5 px-3 text-slate-500">${p.comentarios_cliente || '—'}</td>
                            </tr>
                        `;
                    });

                    const btnCotizar = (s.esta_lista && !s.no_cotizacion && !s.tiene_ceros) ? `
                        <button onclick="asignarNoCotizacion(${s.id})" class="bg-blue-900 hover:bg-blue-800 text-white font-semibold text-xs px-4 py-2 rounded-lg transition shadow-sm">
                            <i class="fa-solid fa-tag"></i> Asignar No. Cotización
                        </button>
                    ` : (s.no_cotizacion ? `
                        <span class="font-bold text-emerald-800 bg-emerald-100 px-3 py-1.5 rounded-lg text-xs"><i class="fa-solid fa-circle-check"></i> Cotización: ${s.no_cotizacion}</span>
                    ` : `
                        <button disabled class="bg-slate-300 text-slate-500 font-semibold text-xs px-4 py-2 rounded-lg cursor-not-allowed">
                            <i class="fa-solid fa-lock"></i> Asignar Bloqueado (${s.tiene_ceros ? 'Precios en $0.00' : 'Faltan Áreas'})
                        </button>
                    `);

                    const btnDescargarPDF = s.no_cotizacion ? `
                        <a href="/api/pdf/cotizacion/${s.id}" target="_blank" class="bg-emerald-700 hover:bg-emerald-800 text-white font-semibold text-xs px-4 py-2 rounded-lg transition shadow-sm inline-flex items-center gap-1.5">
                            <i class="fa-solid fa-file-pdf"></i> Descargar Cotización PDF (Carta)
                        </a>
                        <button onclick="enviarCliente(${s.id})" class="bg-indigo-900 hover:bg-indigo-800 text-white font-semibold text-xs px-4 py-2 rounded-lg transition shadow-sm">
                            <i class="fa-solid fa-paper-plane"></i> Despachar al Cliente (Pasa a Aceptación)
                        </button>
                    ` : '';

                    html += `
                    <div class="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
                        <div class="flex justify-between items-start border-b border-slate-100 pb-3 mb-4">
                            <div>
                                <span class="bg-slate-100 text-slate-700 text-xs px-2.5 py-1 rounded font-bold">Folio: ${s.no_folio}</span>
                                <span class="bg-blue-100 text-blue-900 text-xs px-2.5 py-1 rounded font-bold ml-1">Solicitud: ${s.no_solicitud}</span>
                                <h3 class="text-base font-bold text-slate-900 mt-1">${s.cliente}</h3>
                                <p class="text-xs text-slate-500">${s.representante || ''} &bull; ${s.correo || ''}</p>
                            </div>
                            <div class="text-right">
                                <span class="text-xs font-semibold px-2.5 py-1 rounded ${s.esta_lista ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800'}">
                                    ${s.esta_lista ? '✅ Áreas Técnicas Concluidas' : '⏳ Esperando Respuestas'}
                                </span>
                            </div>
                        </div>

                        ${cerosAlert}

                        <table class="w-full text-left border-collapse mb-4">
                            <thead>
                                <tr class="bg-slate-50 text-slate-600 text-xs border-b border-slate-200">
                                    <th class="py-2 px-3">Part.</th>
                                    <th class="py-2 px-3">Equipo</th>
                                    <th class="py-2 px-3">Servicio de Calibración</th>
                                    <th class="py-2 px-3 text-center">Cant.</th>
                                    <th class="py-2 px-3 text-right">Costo Unitario</th>
                                    <th class="py-2 px-3 text-right">Costo Total</th>
                                    <th class="py-2 px-3">Condiciones / Comentarios Cliente</th>
                                </tr>
                            </thead>
                            <tbody>${tableRows}</tbody>
                        </table>

                        <div class="flex justify-between items-center bg-slate-50 p-4 rounded-xl border border-slate-200">
                            <div class="flex space-x-3">
                                ${btnCotizar}
                                ${btnDescargarPDF}
                            </div>
                            <div class="text-right text-xs space-y-1">
                                <div>Subtotal: <span class="font-bold text-slate-800">$${s.subtotal.toLocaleString('en-US', {minimumFractionDigits: 2})}</span></div>
                                <div>IVA (16%): <span class="font-bold text-slate-800">$${s.iva.toLocaleString('en-US', {minimumFractionDigits: 2})}</span></div>
                                <div class="text-sm font-bold text-blue-900 border-t border-slate-300 pt-1">Total General: $${s.total.toLocaleString('en-US', {minimumFractionDigits: 2})} M.N.</div>
                            </div>
                        </div>
                    </div>
                    `;
                });
                container.innerHTML = html;
            } catch (err) {
                container.innerHTML = `<div class="text-red-700">Error al cargar cotizaciones: ${err.message}</div>`;
            }
        }

        async function asignarNoCotizacion(solicitudId) {
            try {
                const res = await fetch('/api/ssi/asignar-numero-cotizacion', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({solicitud_id: solicitudId})
                });
                let data = null;
                const contentType = res.headers.get("content-type") || "";
                if (contentType.includes("application/json")) {
                    data = await res.json();
                } else {
                    const text = await res.text();
                    data = { detail: text || `Error del servidor (${res.status})` };
                }
                if (res.ok) {
                    alert(`No. de Cotización ${data.no_cotizacion} asignado con éxito.`);
                    loadCotizacionesSSI();
                } else {
                    alert(`Error: ${data.detail || 'No se pudo asignar cotización'}`);
                }
            } catch (err) {
                alert(`Error de red: ${err.message}`);
            }
        }

        async function enviarCliente(solicitudId) {
            try {
                const res = await fetch('/api/ssi/enviar-cliente', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({solicitud_id: solicitudId})
                });
                if (res.ok) {
                    alert("Cotización despachada al cliente. Pasa a la fase de aceptación.");
                    loadCotizacionesSSI();
                    actualizarContadoresSSI();
                }
            } catch (err) {
                alert(`Error: ${err.message}`);
            }
        }

        // ========================================================
        // SSI PESTAÑA 4: ACEPTACIÓN Y PROGRAMACIÓN
        // ========================================================

        async function loadProgramacionSSI() {
            const container = document.getElementById('programacion-ssi-container');
            container.innerHTML = '<div class="text-center py-6 text-slate-500"><i class="fa-solid fa-spinner fa-spin"></i> Cargando solicitudes en programación...</div>';
            try {
                const res = await fetch('/api/ssi/solicitudes-programacion');
                const list = await res.json();
                document.getElementById('badge-prog').innerText = list.length;
                if (list.length === 0) {
                    container.innerHTML = '<div class="bg-white p-6 rounded-xl text-center text-slate-500">No hay solicitudes activas en fase de aceptación o programación.</div>';
                    return;
                }
                let html = '';
                list.forEach(s => {
                    if (s.estado === 'COTIZACION_ENVIADA') {
                        let chkPartidas = '';
                        s.sub_solicitudes.forEach(sub => {
                            sub.partidas.forEach(p => {
                                chkPartidas += `
                                    <div class="flex items-center justify-between p-2.5 bg-slate-50 rounded-lg text-xs mb-2 border border-slate-200">
                                        <label class="flex items-center space-x-2 cursor-pointer font-medium text-slate-800">
                                            <input type="checkbox" id="chk_p_${p.id}" checked class="rounded text-blue-900 w-4 h-4">
                                            <span><strong>Partida ${p.numero_partida}:</strong> ${p.descripcion_equipo} &bull; <em>${p.descripcion_servicio}</em></span>
                                        </label>
                                        <span class="font-bold text-slate-900">$${parseFloat(p.precio_total || 0).toLocaleString('en-US', {minimumFractionDigits: 2})}</span>
                                    </div>
                                `;
                            });
                        });

                        html += `
                        <div class="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
                            <div class="flex justify-between items-center border-b border-slate-100 pb-3 mb-3">
                                <div>
                                    <span class="bg-blue-100 text-blue-900 text-xs px-2.5 py-1 rounded font-bold">Folio: ${s.no_folio}</span>
                                    <span class="font-bold text-slate-900 ml-2">${s.cliente}</span>
                                    <span class="text-xs text-emerald-800 font-bold ml-2">Cotización: ${s.no_cotizacion}</span>
                                </div>
                                <span class="text-xs bg-amber-100 text-amber-800 font-bold px-2 py-1 rounded">Fase 1: Esperando Aceptación</span>
                            </div>
                            <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                                <div>
                                    <label class="block text-xs font-bold text-slate-700 mb-1">No. Orden de Compra u Oficio de Aceptación:</label>
                                    <input type="text" id="oc_input_${s.id}" placeholder="Ej. OC-2026-0812 / OF-CLI-554" class="w-full text-xs border border-slate-300 rounded-lg p-2.5 font-medium">
                                </div>
                                <div>
                                    <label class="block text-xs font-bold text-slate-700 mb-1">Fecha de Aceptación:</label>
                                    <input type="date" id="date_input_${s.id}" value="${new Date().toISOString().split('T')[0]}" class="w-full text-xs border border-slate-300 rounded-lg p-2.5 font-medium">
                                </div>
                            </div>
                            <div class="mb-4">
                                <p class="text-xs text-slate-600 mb-2 font-semibold">Seleccione las partidas aprobadas por el cliente:</p>
                                ${chkPartidas}
                            </div>
                            <button onclick="confirmarAceptacionCliente(${s.id})" class="bg-blue-900 hover:bg-blue-800 text-white font-semibold text-xs px-4 py-2.5 rounded-lg transition shadow-sm">
                                <i class="fa-solid fa-arrow-right"></i> Confirmar Aceptación y Turnar a Programación con CS-AT
                            </button>
                        </div>
                        `;
                    } else {
                        // En programación de fechas o con propuesta
                        let progBlocks = '';
                        let tienePropuesta = false;
                        s.sub_solicitudes.forEach(sub => {
                            if (sub.estado === 'PROGRAMA_PROPUESTO') tienePropuesta = true;
                            let rowsP = '';
                            sub.partidas.forEach(p => {
                                rowsP += `
                                    <tr class="text-xs border-b border-slate-100">
                                        <td class="py-2 px-3 font-bold">${p.numero_partida}</td>
                                        <td class="py-2 px-3">${p.descripcion_servicio}</td>
                                        <td class="py-2 px-3 text-emerald-800 font-semibold">${p.fecha_recepcion_equipo || 'Pendiente'}</td>
                                        <td class="py-2 px-3 font-semibold">${p.fecha_inicio_calibracion || 'Pendiente'}</td>
                                        <td class="py-2 px-3 font-semibold">${p.fecha_entrega_equipo || 'Pendiente'}</td>
                                    </tr>
                                `;
                            });

                            const btnPdfProg = (sub.estado === 'PROGRAMA_PROPUESTO' || sub.estado === 'PROGRAMA_CONFIRMADO') ? `
                                <a href="/api/pdf/programacion/${sub.id}" target="_blank" class="bg-emerald-700 hover:bg-emerald-800 text-white font-semibold text-xs px-3 py-1.5 rounded-md transition shadow-sm inline-flex items-center gap-1.5">
                                    <i class="fa-solid fa-file-pdf"></i> Descargar Propuesta PDF (${sub.clave_area})
                                </a>
                            ` : '';

                            progBlocks += `
                                <div class="bg-slate-50 p-4 rounded-xl border border-slate-200 mb-3">
                                    <div class="flex justify-between items-center mb-2">
                                        <span class="text-xs font-bold text-slate-800">División Técnica ${sub.clave_area} - ${sub.nombre_area || ''}</span>
                                        <span class="text-xs font-semibold px-2 py-0.5 rounded bg-blue-100 text-blue-900">${sub.estado}</span>
                                    </div>
                                    <table class="w-full text-left mb-3">
                                        <thead>
                                            <tr class="text-xs text-slate-500 border-b border-slate-200">
                                                <th class="py-1 px-3">Part.</th>
                                                <th class="py-1 px-3">Servicio</th>
                                                <th class="py-1 px-3">Recepción (-2 días)</th>
                                                <th class="py-1 px-3">Inicio Calibración</th>
                                                <th class="py-1 px-3">Entrega / Fin</th>
                                            </tr>
                                        </thead>
                                        <tbody>${rowsP}</tbody>
                                    </table>
                                    <div>${btnPdfProg}</div>
                                </div>
                            `;
                        });

                        const btnAprobarPropuesta = tienePropuesta ? `
                            <button onclick="aprobarPropuestaFechasSSI(${s.id})" class="bg-indigo-900 hover:bg-indigo-800 text-white font-bold text-xs px-4 py-2 rounded-lg transition shadow-sm">
                                <i class="fa-solid fa-paper-plane mr-1"></i> Aprobar Propuesta de Programa y Despachar al Cliente
                            </button>
                        ` : '';

                        html += `
                        <div class="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
                            <div class="flex justify-between items-center border-b border-slate-100 pb-3 mb-4">
                                <div>
                                    <span class="bg-blue-100 text-blue-900 text-xs px-2.5 py-1 rounded font-bold">Folio: ${s.no_folio}</span>
                                    <span class="font-bold text-slate-900 ml-2">${s.cliente}</span>
                                    <span class="text-xs text-slate-500 ml-2">OC: ${s.orden_compra_cliente || 'N/A'}</span>
                                </div>
                                <span class="text-xs font-bold px-2.5 py-1 rounded bg-blue-50 text-blue-800">Fase 2: ${s.estado}</span>
                            </div>
                            ${progBlocks}
                            <div class="mt-2">${btnAprobarPropuesta}</div>
                        </div>
                        `;
                    }
                });
                container.innerHTML = html;
            } catch (err) {
                container.innerHTML = `<div class="text-red-700">Error al cargar: ${err.message}</div>`;
            }
        }

        async function confirmarAceptacionCliente(solicitudId) {
            const oc = document.getElementById(`oc_input_${solicitudId}`).value;
            const fAcep = document.getElementById(`date_input_${solicitudId}`).value;
            
            const selMap = {};
            const checkboxes = document.querySelectorAll(`[id^="chk_p_"]`);
            checkboxes.forEach(cb => {
                const pid = cb.id.replace('chk_p_', '');
                selMap[pid] = cb.checked;
            });

            try {
                const res = await fetch('/api/ssi/aceptar-partidas-cliente', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        solicitud_id: solicitudId,
                        orden_compra: oc,
                        fecha_aceptacion: fAcep,
                        partidas_seleccionadas: selMap
                    })
                });
                let data = null;
                const contentType = res.headers.get("content-type") || "";
                if (contentType.includes("application/json")) {
                    data = await res.json();
                } else {
                    const text = await res.text();
                    data = { detail: text || `Error del servidor (${res.status})` };
                }
                if (res.ok) {
                    alert(`Aceptación confirmada (${data.aceptadas} partidas turnadas a CS-AT).`);
                    loadProgramacionSSI();
                } else {
                    alert(`Error: ${data.detail || 'No se pudo registrar'}`);
                }
            } catch (err) {
                alert(`Error de red: ${err.message}`);
            }
        }

        async function aprobarPropuestaFechasSSI(solicitudId) {
            try {
                const res = await fetch('/api/ssi/aprobar-propuesta-fechas', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ solicitud_id: solicitudId })
                });
                let data = null;
                const contentType = res.headers.get("content-type") || "";
                if (contentType.includes("application/json")) {
                    data = await res.json();
                } else {
                    const text = await res.text();
                    data = { detail: text || `Error del servidor (${res.status})` };
                }
                if (res.ok) {
                    alert(data.message);
                    loadProgramacionSSI();
                } else {
                    alert("Error: " + (data.detail || "No se pudo aprobar"));
                }
            } catch (err) {
                alert(`Error: ${err.message}`);
            }
        }

        // ========================================================
        // SSI PESTAÑA 5: CONTRATOS Y CONFIRMACIÓN
        // ========================================================

        async function loadConfirmacionSSI() {
            const container = document.getElementById('confirmacion-ssi-container');
            container.innerHTML = '<div class="text-center py-6 text-slate-500"><i class="fa-solid fa-spinner fa-spin"></i> Cargando contratos...</div>';
            try {
                const res = await fetch('/api/ssi/solicitudes-confirmacion');
                const list = await res.json();
                if (list.length === 0) {
                    container.innerHTML = '<div class="bg-white p-6 rounded-xl text-center text-slate-500">No hay contratos pendientes de formalizar.</div>';
                    return;
                }
                let html = '';
                list.forEach(s => {
                    let btnsContratos = '';
                    s.sub_solicitudes.forEach(sub => {
                        btnsContratos += `
                            <a href="/api/pdf/contrato/${sub.id}" target="_blank" class="bg-blue-900 hover:bg-blue-800 text-white font-semibold text-xs px-3 py-1.5 rounded-md transition shadow-sm inline-flex items-center gap-1.5 mr-2 mb-2">
                                <i class="fa-solid fa-file-contract"></i> Descargar Contrato Oficial Carta (${sub.clave_area})
                            </a>
                        `;
                    });

                    const btnConfirmarDef = s.estado !== 'CONFIRMADA_CONCLUIDA' ? `
                        <div class="mt-4 p-4 bg-slate-50 border border-slate-200 rounded-xl space-y-3">
                            <h4 class="text-xs font-bold text-slate-800">Formalización del Servicio:</h4>
                            <div class="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                                <div>
                                    <label class="block font-bold text-slate-700 mb-1">Modalidad de Retorno:</label>
                                    <select id="retorno_${s.id}" class="w-full bg-white border border-slate-300 rounded-lg p-2">
                                        <option value="RECOLECCION_CENAM">Recolección por parte del cliente en instalaciones del CENAM</option>
                                        <option value="GUIA_PREPAGADA">Retorno por paquetería con guía prepagada por el cliente</option>
                                        <option value="EN_SITIO">Servicio realizado en sitio (IN SITU)</option>
                                    </select>
                                </div>
                                <div>
                                    <label class="block font-bold text-slate-700 mb-1">Representante Legal CENAM:</label>
                                    <input type="text" id="rep_cenam_${s.id}" value="${s.representante_legal_cenam || 'Dr. René Carranza'}" class="w-full bg-white border border-slate-300 rounded-lg p-2">
                                </div>
                            </div>
                            <button onclick="confirmarServicioDefinitivo(${s.id})" class="bg-emerald-700 hover:bg-emerald-800 text-white font-bold text-xs px-4 py-2 rounded-lg transition shadow-sm">
                                <i class="fa-solid fa-lock mr-1"></i> Confirmar Reserva Definitiva con Laboratorios
                            </button>
                        </div>
                    ` : `
                        <div class="mt-2 text-xs font-bold text-emerald-800 bg-emerald-50 p-3 rounded-lg border border-emerald-200">
                            🔒 Reserva Definitiva Confirmada y Notificada a Laboratorios.
                        </div>
                    `;

                    html += `
                    <div class="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
                        <div class="flex justify-between items-center border-b border-slate-100 pb-3 mb-3">
                            <div>
                                <span class="bg-blue-100 text-blue-900 text-xs px-2.5 py-1 rounded font-bold">Folio: ${s.no_folio}</span>
                                <span class="font-bold text-slate-900 ml-2">${s.cliente}</span>
                            </div>
                            <span class="text-xs bg-emerald-100 text-emerald-800 font-bold px-2 py-1 rounded">Listo para Formalizar</span>
                        </div>
                        <div class="p-3 bg-slate-50 rounded-xl mb-2">
                            <p class="text-xs font-semibold text-slate-700 mb-2">Documentos Oficiales por Área Técnica:</p>
                            ${btnsContratos}
                        </div>
                        ${btnConfirmarDef}
                    </div>
                    `;
                });
                container.innerHTML = html;
            } catch (err) {
                container.innerHTML = `<div class="text-red-700">Error: ${err.message}</div>`;
            }
        }

        async function confirmarServicioDefinitivo(solicitudId) {
            const retorno = document.getElementById(`retorno_${solicitudId}`).value;
            const repCenam = document.getElementById(`rep_cenam_${solicitudId}`).value;
            try {
                const res = await fetch('/api/ssi/confirmar-servicio', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        solicitud_id: solicitudId,
                        modalidad_retorno: retorno,
                        representante_legal_cenam: repCenam
                    })
                });
                let data = null;
                const contentType = res.headers.get("content-type") || "";
                if (contentType.includes("application/json")) {
                    data = await res.json();
                } else {
                    const text = await res.text();
                    data = { detail: text || `Error del servidor (${res.status})` };
                }
                if (res.ok) {
                    alert(data.message);
                    loadConfirmacionSSI();
                } else {
                    alert("Error: " + (data.detail || "No se pudo confirmar"));
                }
            } catch (err) {
                alert(`Error de red: ${err.message}`);
            }
        }

        // ========================================================
        // CS-AT: COTIZACIÓN METROLÓGICA (ETAPA 2)
        // ========================================================

        async function loadPendingAT() {
            const container = document.getElementById('at-cotizaciones-container');
            container.innerHTML = '<div class="text-center py-6 text-slate-500"><i class="fa-solid fa-spinner fa-spin"></i> Cargando partidas del área...</div>';
            try {
                const servRes = await fetch(`/api/catalogos/servicios?clave_area=${currentAreaAT}`);
                const servsArea = await servRes.json();
                allServicesCache[currentAreaAT] = servsArea;

                const labsRes = await fetch(`/api/catalogos/laboratorios?clave_area=${currentAreaAT}`);
                const labsArea = await labsRes.json();
                allLabsCache[currentAreaAT] = labsArea;

                const res = await fetch(`/api/at/solicitudes-pendientes/${currentAreaAT}`);
                const subs = await res.json();
                if (subs.length === 0) {
                    container.innerHTML = `<div class="bg-emerald-50 text-emerald-800 p-6 rounded-xl text-center font-medium">🎉 No hay solicitudes pendientes de cotizar para la División ${currentAreaAT}. ¡Bandeja al día!</div>`;
                    return;
                }

                let html = '';
                subs.forEach(s => {
                    let partidasHtml = '';
                    s.partidas.forEach(p => {
                        let optServs = '';
                        servsArea.forEach(srv => {
                            const isSel = p.clave_servicio === srv.clave_servicio ? 'selected' : '';
                            optServs += `<option value="${srv.clave_servicio}" data-costo="${srv.costo}" data-supuesto="${srv.supuesto}" ${isSel}>${srv.clave_servicio} - ${srv.supuesto.substring(0, 70)}... ($${parseFloat(srv.costo).toLocaleString('en-US', {minimumFractionDigits: 2})})</option>`;
                        });

                        partidasHtml += `
                            <div class="border border-slate-200 rounded-xl p-4 bg-slate-50 mb-3 text-xs" id="partida_card_${p.id}">
                                <div class="flex justify-between items-start mb-2">
                                    <span class="font-bold text-slate-900 text-sm">Partida ${p.numero_partida}: ${p.descripcion_equipo}</span>
                                    <span class="text-slate-500 font-medium">Marca: ${p.marca || 'N/A'} | Modelo: ${p.modelo || 'N/A'} | Serie: ${p.no_serie || 'N/A'}</span>
                                </div>
                                <!-- Filtro por Laboratorio y Buscador de Servicios -->
                                <div class="mb-2.5 p-2.5 bg-blue-50/70 border border-blue-200 rounded-lg">
                                    <div class="grid grid-cols-1 md:grid-cols-2 gap-2">
                                        <div>
                                            <label class="block text-[11px] font-bold text-blue-950 mb-1">
                                                <i class="fa-solid fa-filter text-blue-800 mr-1"></i> Filtrar por Laboratorio Técnico:
                                            </label>
                                            <select id="lab_filter_${p.id}" onchange="filtrarServiciosPorLaboratorio(${p.id})" class="w-full bg-white border border-blue-300 rounded-lg p-1.5 text-xs font-semibold text-slate-800">
                                                <option value="">-- Todos los Laboratorios del Área (${labsArea.length}) --</option>
                                                ${labsArea.map(l => `<option value="${l.codigo}">${l.codigo} - ${l.descripcion}</option>`).join('')}
                                            </select>
                                        </div>
                                        <div>
                                            <label class="block text-[11px] font-bold text-slate-700 mb-1">
                                                <i class="fa-solid fa-search text-slate-500 mr-1"></i> Buscar en Catálogo (Clave o Texto):
                                            </label>
                                            <input type="text" id="serv_search_${p.id}" oninput="filtrarServiciosPorLaboratorio(${p.id})" placeholder="Escriba palabra clave (ej. calibrador, masa, bloque)..." class="w-full bg-white border border-slate-300 rounded-lg p-1.5 text-xs text-slate-800">
                                        </div>
                                    </div>
                                </div>

                                <div class="grid grid-cols-1 md:grid-cols-4 gap-3 mb-3">
                                    <div class="md:col-span-2">
                                        <label class="block text-slate-700 font-bold mb-1">Servicio del Catálogo Oficial:</label>
                                        <select id="serv_sel_${p.id}" onchange="updateRowPrice(${p.id})" class="w-full bg-white border border-slate-300 rounded-lg p-2 font-medium">
                                            <option value="">-- Seleccione Servicio --</option>
                                            ${optServs}
                                        </select>
                                    </div>
                                    <div>
                                        <label class="block text-slate-700 font-bold mb-1">Cantidad:</label>
                                        <input type="number" id="cant_inp_${p.id}" min="1" value="${p.cantidad || 1}" onchange="updateRowPrice(${p.id})" class="w-full bg-white border border-slate-300 rounded-lg p-2 font-bold text-center">
                                    </div>
                                    <div>
                                        <label class="block text-slate-700 font-bold mb-1">Costo Total ($ M.N.):</label>
                                        <input type="text" id="tot_inp_${p.id}" readonly value="$${parseFloat(p.precio_total || 0).toLocaleString('en-US', {minimumFractionDigits: 2})}" class="w-full bg-slate-100 border border-slate-300 rounded-lg p-2 font-bold text-right text-blue-900">
                                    </div>
                                </div>
                                <div class="grid grid-cols-1 md:grid-cols-2 gap-3 mb-2">
                                    <div>
                                        <label class="block text-slate-600 font-semibold mb-1">Comentarios para SSI (Interno):</label>
                                        <input type="text" id="cssi_inp_${p.id}" value="${p.comentarios_ssi || ''}" placeholder="Notas operativas..." class="w-full bg-white border border-slate-300 rounded-lg p-2">
                                    </div>
                                    <div>
                                        <label class="block text-slate-600 font-semibold mb-1">Comentarios para Cliente (En Cotización Oficial):</label>
                                        <input type="text" id="ccli_inp_${p.id}" value="${p.comentarios_cliente || ''}" placeholder="Condiciones técnicas del servicio..." class="w-full bg-white border border-slate-300 rounded-lg p-2">
                                    </div>
                                </div>
                            </div>
                        `;
                    });

                    html += `
                    <div class="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
                        <div class="flex justify-between items-center border-b border-slate-100 pb-3 mb-4">
                            <div>
                                <span class="bg-blue-100 text-blue-900 text-xs px-2.5 py-1 rounded font-bold">Folio: ${s.no_folio}</span>
                                <span class="bg-slate-100 text-slate-700 text-xs px-2.5 py-1 rounded font-bold ml-1">Solicitud: ${s.no_solicitud}</span>
                                <span class="text-sm font-bold text-slate-900 ml-2">${s.cliente}</span>
                            </div>
                            <div class="flex items-center space-x-2">
                                <button onclick="devolverSolicitudAT(${s.sub_id})" class="text-xs bg-red-50 hover:bg-red-100 text-red-800 border border-red-200 px-3 py-1.5 rounded-lg font-bold">
                                    <i class="fa-solid fa-arrow-rotate-left mr-1"></i> Devolver a SSI
                                </button>
                                <button onclick="consultarEspecialistaAT(${s.sub_id})" class="text-xs bg-amber-50 hover:bg-amber-100 text-amber-800 border border-amber-200 px-3 py-1.5 rounded-lg font-bold">
                                    <i class="fa-solid fa-user-doctor mr-1"></i> Consultar Especialista
                                </button>
                            </div>
                        </div>
                        ${partidasHtml}
                        <button onclick="aprobarCotizacionAT(${s.sub_id})" class="bg-blue-900 hover:bg-blue-800 text-white font-semibold text-xs px-5 py-2.5 rounded-lg transition shadow-sm flex items-center gap-2">
                            <i class="fa-solid fa-check-double"></i> Aprobar y Regresar Cotización a SSI (Validación de Precios)
                        </button>
                    </div>
                    `;
                });
                container.innerHTML = html;
            } catch (err) {
                container.innerHTML = `<div class="text-red-700">Error al cargar solicitudes AT: ${err.message}</div>`;
            }
        }


        function filtrarServiciosPorLaboratorio(partidaId) {
            const labFilter = document.getElementById(`lab_filter_${partidaId}`);
            const searchInput = document.getElementById(`serv_search_${partidaId}`);
            const servSelect = document.getElementById(`serv_sel_${partidaId}`);
            if (!servSelect) return;

            const selectedLab = labFilter ? labFilter.value.trim() : '';
            const query = searchInput ? searchInput.value.toLowerCase().trim() : '';
            const servs = allServicesCache[currentAreaAT] || [];

            let filtered = servs;
            if (selectedLab) {
                filtered = filtered.filter(s => String(s.codigo_laboratorio || '').trim() === selectedLab);
            }
            if (query) {
                filtered = filtered.filter(s => 
                    (s.clave_servicio && s.clave_servicio.toLowerCase().includes(query)) ||
                    (s.supuesto && s.supuesto.toLowerCase().includes(query))
                );
            }

            const currVal = servSelect.value;
            let optHtml = `<option value="">-- Seleccione Servicio (${filtered.length} disponibles) --</option>`;
            filtered.forEach(srv => {
                const isSel = (srv.clave_servicio === currVal) ? 'selected' : '';
                const labPrefix = srv.codigo_laboratorio ? `[${srv.codigo_laboratorio}] ` : '';
                optHtml += `<option value="${srv.clave_servicio}" data-costo="${srv.costo}" data-supuesto="${srv.supuesto}" ${isSel}>${labPrefix}${srv.clave_servicio} - ${srv.supuesto.substring(0, 65)}... ($${parseFloat(srv.costo).toLocaleString('en-US', {minimumFractionDigits: 2})})</option>`;
            });
            servSelect.innerHTML = optHtml;
        }

        function updateRowPrice(partidaId) {
            const sel = document.getElementById(`serv_sel_${partidaId}`);
            const cantInp = document.getElementById(`cant_inp_${partidaId}`);
            const totInp = document.getElementById(`tot_inp_${partidaId}`);
            const selectedOpt = sel.options[sel.selectedIndex];
            const costo = parseFloat(selectedOpt ? selectedOpt.getAttribute('data-costo') || 0.0 : 0.0);
            const cant = parseInt(cantInp.value || 1);
            const tot = costo * cant;
            totInp.value = `$${tot.toLocaleString('en-US', {minimumFractionDigits: 2})}`;
        }

        async function devolverSolicitudAT(subId) {
            const motivo = prompt("Ingrese el motivo técnico por el cual no corresponde a esta área técnica:");
            if (!motivo || !motivo.trim()) return;
            const sug = prompt("Indique el código de área sugerida (ej. 740, 410, 730, 420):", "740");
            try {
                const res = await fetch('/api/at/devolver-a-ssi', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ sub_solicitud_id: subId, motivo_devolucion: motivo, area_sugerida: sug })
                });
                let data = null;
                const contentType = res.headers.get("content-type") || "";
                if (contentType.includes("application/json")) {
                    data = await res.json();
                } else {
                    const text = await res.text();
                    data = { detail: text || `Error del servidor (${res.status})` };
                }
                if (res.ok) {
                    alert(data.message);
                    loadPendingAT();
                } else {
                    alert("Error: " + (data.detail || "No se pudo devolver"));
                }
            } catch (err) {
                alert(`Error: ${err.message}`);
            }
        }

        async function consultarEspecialistaAT(subId) {
            const nombre = prompt("Nombre / Correo del Especialista de Laboratorio:", "especialista@cenam.mx");
            if (!nombre) return;
            const duda = prompt("Duda o pregunta técnica de calibración:");
            if (!duda) return;
            const resp = prompt("Respuesta del especialista (evidencia técnica ISO 17025):", "Viabilidad técnica confirmada con patrones secundarios.");
            try {
                const res = await fetch('/api/at/consultar-especialista', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        sub_solicitud_id: subId,
                        especialista_nombre: nombre,
                        pregunta: duda,
                        respuesta: resp
                    })
                });
                let data = null;
                const contentType = res.headers.get("content-type") || "";
                if (contentType.includes("application/json")) {
                    data = await res.json();
                } else {
                    const text = await res.text();
                    data = { detail: text || `Error del servidor (${res.status})` };
                }
                if (res.ok) {
                    alert(data.message);
                    loadPendingAT();
                }
            } catch (err) {
                alert(`Error: ${err.message}`);
            }
        }

        async function aprobarCotizacionAT(subId) {
            const cards = document.querySelectorAll(`[id^="partida_card_"]`);
            const partidasPayload = [];
            
            for (let card of cards) {
                const pid = card.id.replace('partida_card_', '');
                const sel = document.getElementById(`serv_sel_${pid}`);
                const cantInp = document.getElementById(`cant_inp_${pid}`);
                const cssiInp = document.getElementById(`cssi_inp_${pid}`);
                const ccliInp = document.getElementById(`ccli_inp_${pid}`);
                
                const selectedOpt = sel ? sel.options[sel.selectedIndex] : null;
                const claveServ = sel ? sel.value : '';
                const costo = parseFloat(selectedOpt ? selectedOpt.getAttribute('data-costo') || 0.0 : 0.0);
                const supuesto = selectedOpt ? selectedOpt.getAttribute('data-supuesto') || '' : '';
                const cant = parseInt(cantInp ? cantInp.value || 1 : 1);
                
                partidasPayload.push({
                    id: parseInt(pid),
                    clave_servicio: claveServ,
                    descripcion_servicio: supuesto,
                    precio_unitario: costo,
                    cantidad: cant,
                    comentarios_ssi: cssiInp ? cssiInp.value : '',
                    comentarios_cliente: ccliInp ? ccliInp.value : '',
                    es_no_realizable: 0,
                    es_manual: 0
                });
            }

            try {
                const res = await fetch('/api/at/aprobar-sub-solicitud', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        sub_solicitud_id: subId,
                        partidas: partidasPayload
                    })
                });
                let data = null;
                const contentType = res.headers.get("content-type") || "";
                if (contentType.includes("application/json")) {
                    data = await res.json();
                } else {
                    const text = await res.text();
                    data = { detail: text || `Error del servidor (${res.status})` };
                }
                if (res.ok) {
                    alert("✅ Cotización validada y turnada a SSI exitosamente (Precios verificados).");
                    loadPendingAT();
                } else {
                    const errDetail = data.detail;
                    if (errDetail && errDetail.errores) {
                        alert("❌ Error de Validación:\\n" + errDetail.errores.join("\\n"));
                    } else {
                        alert("Error: " + (data.detail || "No se pudo aprobar"));
                    }
                }
            } catch (err) {
                alert(`Error de red: ${err.message}`);
            }
        }

        // ========================================================
        // CS-AT: PROGRAMACIÓN DE FECHAS (ETAPA 3)
        // ========================================================

        async function loadProgramacionAT() {
            const container = document.getElementById('at-programacion-container');
            container.innerHTML = '<div class="text-center py-6 text-slate-500"><i class="fa-solid fa-spinner fa-spin"></i> Cargando fechas...</div>';
            try {
                const res = await fetch(`/api/at/programacion-fechas/${currentAreaAT}`);
                const subs = await res.json();
                if (subs.length === 0) {
                    container.innerHTML = `<div class="bg-emerald-50 text-emerald-800 p-6 rounded-xl text-center font-medium">🎉 No hay servicios pendientes de programar fechas para el Área ${currentAreaAT}.</div>`;
                    return;
                }

                let html = '';
                subs.forEach(s => {
                    let formFechas = '';
                    s.partidas.forEach(p => {
                        const hoy = new Date();
                        const defIni = new Date(hoy.setDate(hoy.getDate() + 14)).toISOString().split('T')[0];
                        const defRec = new Date(hoy.setDate(hoy.getDate() - 2)).toISOString().split('T')[0];
                        const defFin = new Date(hoy.setDate(hoy.getDate() + 7)).toISOString().split('T')[0];

                        formFechas += `
                            <div class="bg-slate-50 p-4 rounded-xl border border-slate-200 mb-3 text-xs" id="prog_card_${p.id}">
                                <div class="font-bold text-slate-800 mb-2">Partida ${p.numero_partida}: ${p.descripcion_equipo} (${p.descripcion_servicio})</div>
                                <div class="grid grid-cols-1 md:grid-cols-3 gap-3">
                                    <div>
                                        <label class="block font-bold text-slate-700 mb-1">Recepción Equipo (-2 días hábiles):</label>
                                        <input type="date" id="f_rec_${p.id}" value="${p.fecha_recepcion_equipo || defRec}" class="w-full bg-white border border-slate-300 rounded-lg p-2 font-medium">
                                    </div>
                                    <div>
                                        <label class="block font-bold text-slate-700 mb-1">Inicio Calibración *:</label>
                                        <input type="date" id="f_ini_${p.id}" value="${p.fecha_inicio_calibracion || defIni}" class="w-full bg-white border border-slate-300 rounded-lg p-2 font-bold text-blue-900">
                                    </div>
                                    <div>
                                        <label class="block font-bold text-slate-700 mb-1">Entrega / Fin *:</label>
                                        <input type="date" id="f_fin_${p.id}" value="${p.fecha_entrega_equipo || defFin}" class="w-full bg-white border border-slate-300 rounded-lg p-2 font-medium">
                                    </div>
                                </div>
                            </div>
                        `;
                    });

                    html += `
                    <div class="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
                        <div class="flex justify-between items-center border-b border-slate-100 pb-3 mb-3">
                            <div>
                                <span class="bg-blue-100 text-blue-900 text-xs px-2.5 py-1 rounded font-bold">Folio: ${s.no_folio}</span>
                                <span class="font-bold text-slate-900 ml-2">${s.cliente}</span>
                            </div>
                            <span class="text-xs bg-amber-100 text-amber-800 font-bold px-2 py-1 rounded">Asignación de Fechas</span>
                        </div>
                        ${formFechas}
                        <button onclick="enviarFechasAT(${s.sub_id}, ${s.master_id})" class="bg-blue-900 hover:bg-blue-800 text-white font-semibold text-xs px-4 py-2 rounded-lg transition shadow-sm">
                            <i class="fa-solid fa-paper-plane mr-1"></i> Enviar Fechas Programadas a SSI
                        </button>
                    </div>
                    `;
                });
                container.innerHTML = html;
            } catch (err) {
                container.innerHTML = `<div class="text-red-700">Error: ${err.message}</div>`;
            }
        }

        async function enviarFechasAT(subId, masterId) {
            const cards = document.querySelectorAll(`[id^="prog_card_"]`);
            const fechasObj = {};
            cards.forEach(c => {
                const pid = c.id.replace('prog_card_', '');
                fechasObj[pid] = {
                    recepcion: document.getElementById(`f_rec_${pid}`).value,
                    inicio: document.getElementById(`f_ini_${pid}`).value,
                    entrega: document.getElementById(`f_fin_${pid}`).value,
                    limite: document.getElementById(`f_fin_${pid}`).value
                };
            });

            try {
                const res = await fetch('/api/at/programar-fechas', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        sub_solicitud_id: subId,
                        master_id: masterId,
                        fechas: fechasObj
                    })
                });
                if (res.ok) {
                    alert("🗓️ Fechas de calibración enviadas a SSI con éxito.");
                    loadProgramacionAT();
                }
            } catch (err) {
                alert(`Error: ${err.message}`);
            }
        }

        // ========================================================
        // CS-AT: CALENDARIO CONFIRMADO (PESTAÑA 3)
        // ========================================================

        async function loadCalendarioAT() {
            const container = document.getElementById('at-calendario-container');
            container.innerHTML = '<div class="text-center py-6 text-slate-500"><i class="fa-solid fa-spinner fa-spin"></i> Cargando calendario de reservas...</div>';
            try {
                const res = await fetch(`/api/at/calendario-confirmado/${currentAreaAT}`);
                const rows = await res.json();
                if (rows.length === 0) {
                    container.innerHTML = `<div class="bg-white p-6 rounded-xl text-center text-slate-500">Aún no hay servicios confirmados en el calendario de la División ${currentAreaAT}.</div>`;
                    return;
                }

                let trs = '';
                rows.forEach(r => {
                    trs += `
                        <tr class="text-xs border-b border-slate-100">
                            <td class="py-2.5 px-3 font-bold text-blue-900">${r.no_folio}</td>
                            <td class="py-2.5 px-3 font-bold text-emerald-800">${r.no_cotizacion || '—'}</td>
                            <td class="py-2.5 px-3 font-semibold text-slate-800">${r.cliente}</td>
                            <td class="py-2.5 px-3 text-slate-600">${r.fecha_recepcion_prog || '—'}</td>
                            <td class="py-2.5 px-3 font-bold text-blue-900">${r.fecha_inicio_prog || '—'}</td>
                            <td class="py-2.5 px-3 font-semibold text-slate-800">${r.fecha_entrega_prog || '—'}</td>
                            <td class="py-2.5 px-3"><span class="bg-emerald-100 text-emerald-800 px-2 py-0.5 rounded text-xs font-bold">🔒 RESERVA CONFIRMADA</span></td>
                        </tr>
                    `;
                });

                container.innerHTML = `
                    <div class="bg-white rounded-xl shadow-sm border border-slate-200 overflow-x-auto">
                        <table class="w-full text-left">
                            <thead>
                                <tr class="bg-slate-50 text-slate-600 text-xs border-b border-slate-200 font-bold">
                                    <th class="py-2 px-3">Folio</th>
                                    <th class="py-2 px-3">Cotización</th>
                                    <th class="py-2 px-3">Cliente</th>
                                    <th class="py-2 px-3">Recepción</th>
                                    <th class="py-2 px-3">Inicio</th>
                                    <th class="py-2 px-3">Entrega</th>
                                    <th class="py-2 px-3">Estado</th>
                                </tr>
                            </thead>
                            <tbody>${trs}</tbody>
                        </table>
                    </div>
                `;
            } catch (err) {
                container.innerHTML = `<div class="text-red-700">Error: ${err.message}</div>`;
            }
        }

        // ========================================================
        // MANTENIMIENTO: LIMPIEZA A ESTADO CERO
        // ========================================================

        async function limpiarBaseDatos() {
            if (!confirm("¿Está seguro de reiniciar el sistema operativo a estado cero?\\n\\nSe eliminarán solicitudes de prueba y se reiniciará el contador a 0001-2026PR.\\nLos catálogos (1,036 servicios, 294 laboratorios, 15 áreas) quedan 100% protegidos.")) return;
            const statusDiv = document.getElementById('maint-status');
            statusDiv.innerHTML = '<span class="text-blue-700"><i class="fa-solid fa-spinner fa-spin"></i> Ejecutando limpieza segura...</span>';
            try {
                const res = await fetch('/api/mantenimiento/limpiar-bd', {method: 'POST'});
                let data = null;
                const contentType = res.headers.get("content-type") || "";
                if (contentType.includes("application/json")) {
                    data = await res.json();
                } else {
                    const text = await res.text();
                    data = { detail: text || `Error del servidor (${res.status})` };
                }
                if (res.ok) {
                    statusDiv.innerHTML = `<div class="p-4 bg-emerald-50 text-emerald-800 rounded-lg text-xs font-semibold">✅ ${data.message}</div>`;
                    inicializarFormularioVacio();
                    actualizarContadoresSSI();
                } else {
                    statusDiv.innerHTML = `<div class="p-4 bg-red-50 text-red-800 rounded-lg text-xs font-semibold">Error al limpiar.</div>`;
                }
            } catch (err) {
                statusDiv.innerHTML = `<div class="text-red-700 text-xs">Error de conexión: ${err.message}</div>`;
            }
        }
    </script>
</body>
</html>
"""

