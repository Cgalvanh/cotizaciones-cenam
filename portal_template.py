"""
Plantillas HTML interactivas para:
1. Formulario Público de Captura con Quality Gate / Previsualización y Acuse Oficial.
2. Portal de Clientes con Autenticación por Código OTP (6 dígitos) y Módulo de Aceptación Digital.
"""

SOLICITUD_PUBLIC_HTML = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CENAM - Solicitud de Servicios Metrológicos</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        :root { --cenam-navy: #1e3a8a; --cenam-gold: #8a6d3b; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f8fafc; color: #1e293b; }
        .hidden { display: none !important; }
    </style>
</head>
<body class="min-h-screen flex flex-col justify-between">
    <!-- Header Institucional -->
    <header class="bg-slate-900 text-white shadow-md border-b-4 border-amber-600">
        <div class="max-w-6xl mx-auto px-4 py-4 flex flex-col sm:flex-row justify-between items-center gap-3">
            <div class="flex items-center space-x-3">
                <div class="w-10 h-10 rounded-lg bg-amber-600 flex items-center justify-center font-bold text-slate-900 text-xl shadow">
                    <i class="fa-solid fa-scale-balanced text-white"></i>
                </div>
                <div>
                    <h1 class="text-base sm:text-lg font-extrabold tracking-tight">CENTRO NACIONAL DE METROLOGÍA</h1>
                    <p class="text-xs text-slate-300">Ventanilla Digital de Servicios de Calibración (CENAM)</p>
                </div>
            </div>
            <div class="flex items-center gap-3">
                <a href="/portal" class="text-xs bg-slate-800 hover:bg-slate-700 text-amber-400 font-semibold px-3 py-2 rounded-lg border border-amber-500/40 transition flex items-center gap-1.5">
                    <i class="fa-solid fa-user-shield"></i> Portal de Clientes / Seguimiento
                </a>
                <a href="/" class="text-xs text-slate-400 hover:text-white px-2 py-1">
                    <i class="fa-solid fa-lock"></i> Acceso Personal CENAM
                </a>
            </div>
        </div>
    </header>

    <!-- Contenido Principal con Stepper -->
    <main class="max-w-4xl mx-auto w-full px-4 py-8 flex-1">
        <!-- Indicador de Pasos -->
        <div class="mb-8">
            <div class="flex justify-between items-center relative">
                <div class="w-full absolute top-1/2 -translate-y-1/2 left-0 h-1 bg-slate-200 z-0"></div>
                <div id="step-bar" class="w-0 absolute top-1/2 -translate-y-1/2 left-0 h-1 bg-blue-900 z-0 transition-all duration-300"></div>

                <div class="step-node relative z-10 flex flex-col items-center">
                    <div id="badge-step-1" class="w-9 h-9 rounded-full bg-blue-900 text-white font-bold flex items-center justify-center text-sm shadow ring-4 ring-white">1</div>
                    <span class="text-xs font-bold mt-2 text-blue-900">Datos Cliente</span>
                </div>
                <div class="step-node relative z-10 flex flex-col items-center">
                    <div id="badge-step-2" class="w-9 h-9 rounded-full bg-slate-200 text-slate-600 font-bold flex items-center justify-center text-sm shadow ring-4 ring-white">2</div>
                    <span class="text-xs font-semibold mt-2 text-slate-500">Equipos a Calibrar</span>
                </div>
                <div class="step-node relative z-10 flex flex-col items-center">
                    <div id="badge-step-3" class="w-9 h-9 rounded-full bg-slate-200 text-slate-600 font-bold flex items-center justify-center text-sm shadow ring-4 ring-white">3</div>
                    <span class="text-xs font-semibold mt-2 text-slate-500">Previsualización</span>
                </div>
                <div class="step-node relative z-10 flex flex-col items-center">
                    <div id="badge-step-4" class="w-9 h-9 rounded-full bg-slate-200 text-slate-600 font-bold flex items-center justify-center text-sm shadow ring-4 ring-white">4</div>
                    <span class="text-xs font-semibold mt-2 text-slate-500">Acuse Oficial</span>
                </div>
            </div>
        </div>

        <!-- PASO 1: DATOS FISCALES Y DE CONTACTO -->
        <div id="panel-step-1" class="bg-white rounded-2xl shadow-sm border border-slate-200 p-6 sm:p-8">
            <div class="border-b border-slate-200 pb-4 mb-6">
                <h2 class="text-xl font-bold text-slate-900 flex items-center gap-2">
                    <i class="fa-solid fa-building text-blue-900"></i> Paso 1: Datos de la Empresa y Contacto
                </h2>
                <p class="text-xs text-slate-500 mt-1">Ingrese los datos oficiales para la emisión de la cotización y el comprobante fiscal.</p>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div class="md:col-span-2">
                    <label class="block text-xs font-bold text-slate-700 mb-1">Nombre o Razón Social del Cliente / Empresa *</label>
                    <input type="text" id="cli-nombre" placeholder="Ej. METROLOGÍA INDUSTRIAL DE MÉXICO S.A. DE C.V." class="w-full bg-slate-50 border border-slate-300 rounded-lg p-2.5 text-sm focus:ring-2 focus:ring-blue-900 focus:bg-white outline-none">
                </div>
                <div>
                    <label class="block text-xs font-bold text-slate-700 mb-1">RFC (Registro Federal de Contribuyentes) *</label>
                    <input type="text" id="cli-rfc" placeholder="MIM901015AB1" maxlength="13" class="w-full uppercase bg-slate-50 border border-slate-300 rounded-lg p-2.5 text-sm focus:ring-2 focus:ring-blue-900 focus:bg-white outline-none">
                </div>
                <div>
                    <label class="block text-xs font-bold text-slate-700 mb-1">Nombre del Contacto / Representante *</label>
                    <input type="text" id="cli-rep" placeholder="Ing. Carlos Mendoza Silva" class="w-full bg-slate-50 border border-slate-300 rounded-lg p-2.5 text-sm focus:ring-2 focus:ring-blue-900 focus:bg-white outline-none">
                </div>
                <div>
                    <label class="block text-xs font-bold text-slate-700 mb-1">Correo Electrónico Corporativo *</label>
                    <input type="email" id="cli-correo" placeholder="cmendoza@empresa.com" class="w-full bg-slate-50 border border-slate-300 rounded-lg p-2.5 text-sm focus:ring-2 focus:ring-blue-900 focus:bg-white outline-none">
                    <span class="text-[11px] text-slate-500">A este correo se le enviará la cotización oficial y su código de acceso.</span>
                </div>
                <div>
                    <label class="block text-xs font-bold text-slate-700 mb-1">Teléfono de Contacto (con extensión) *</label>
                    <input type="tel" id="cli-tel" placeholder="(442) 211-0500 ext. 123" class="w-full bg-slate-50 border border-slate-300 rounded-lg p-2.5 text-sm focus:ring-2 focus:ring-blue-900 focus:bg-white outline-none">
                </div>
                <div>
                    <label class="block text-xs font-bold text-slate-700 mb-1">País</label>
                    <input type="text" id="cli-pais" value="México" class="w-full bg-slate-50 border border-slate-300 rounded-lg p-2.5 text-sm">
                </div>
                <div class="flex items-center mt-6">
                    <label class="inline-flex items-center cursor-pointer">
                        <input type="checkbox" id="cli-iva" checked class="w-4 h-4 text-blue-900 rounded border-slate-300 focus:ring-blue-900">
                        <span class="ml-2 text-xs font-semibold text-slate-700">Aplica I.V.A. (16% Nacional)</span>
                    </label>
                </div>
                <div class="md:col-span-2">
                    <label class="block text-xs font-bold text-slate-700 mb-1">Dirección de Planta / Instalaciones (para calibraciones en sitio)</label>
                    <input type="text" id="cli-dir" placeholder="Av. Industrial No. 405, Parque Industrial Querétaro, Qro." class="w-full bg-slate-50 border border-slate-300 rounded-lg p-2.5 text-sm focus:ring-2 focus:ring-blue-900 focus:bg-white outline-none">
                </div>
            </div>

            <div class="mt-8 flex justify-end">
                <button onclick="irAPaso2()" class="bg-blue-900 hover:bg-blue-800 text-white font-bold text-sm px-6 py-3 rounded-xl shadow-md transition flex items-center gap-2">
                    Continuar a Equipos a Calibrar <i class="fa-solid fa-arrow-right"></i>
                </button>
            </div>
        </div>

        <!-- PASO 2: REGISTRO DE INSTRUMENTOS -->
        <div id="panel-step-2" class="hidden bg-white rounded-2xl shadow-sm border border-slate-200 p-6 sm:p-8">
            <div class="border-b border-slate-200 pb-4 mb-6 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3">
                <div>
                    <h2 class="text-xl font-bold text-slate-900 flex items-center gap-2">
                        <i class="fa-solid fa-screwdriver-wrench text-blue-900"></i> Paso 2: Equipos e Instrumentos a Calibrar
                    </h2>
                    <p class="text-xs text-slate-500 mt-1">Agregue los instrumentos de medición que desea someter a calibración.</p>
                </div>
                <button onclick="agregarInstrumento()" class="bg-amber-600 hover:bg-amber-500 text-white font-bold text-xs px-4 py-2.5 rounded-lg shadow-sm transition flex items-center gap-1.5">
                    <i class="fa-solid fa-plus"></i> Agregar Otro Instrumento
                </button>
            </div>

            <!-- Contenedor dinámico de instrumentos -->
            <div id="instrumentos-container" class="space-y-4"></div>

            <div class="mt-8 flex justify-between items-center pt-4 border-t border-slate-200">
                <button onclick="irAPaso(1)" class="bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold text-sm px-5 py-2.5 rounded-xl transition flex items-center gap-2">
                    <i class="fa-solid fa-arrow-left"></i> Regresar a Datos Cliente
                </button>
                <button onclick="irAPaso3()" class="bg-blue-900 hover:bg-blue-800 text-white font-bold text-sm px-6 py-3 rounded-xl shadow-md transition flex items-center gap-2">
                    Ver Previsualización Completa <i class="fa-solid fa-arrow-right"></i>
                </button>
            </div>
        </div>

        <!-- PASO 3: PREVISUALIZACIÓN Y QUALITY GATE -->
        <div id="panel-step-3" class="hidden bg-white rounded-2xl shadow-sm border border-slate-200 p-6 sm:p-8">
            <div class="border-b border-slate-200 pb-4 mb-6">
                <div class="bg-amber-50 border-l-4 border-amber-500 p-4 rounded-r-lg mb-4">
                    <p class="text-xs text-amber-800 font-semibold">
                        <i class="fa-solid fa-circle-exclamation mr-1.5"></i> <strong>Verificación de Calidad:</strong> Revise detalladamente los datos de su empresa y la lista de equipos antes de enviar. Al confirmar, el sistema generará automáticamente su <strong>Folio Oficial de CENAM</strong>.
                    </p>
                </div>
                <h2 class="text-xl font-bold text-slate-900 flex items-center gap-2">
                    <i class="fa-solid fa-clipboard-check text-blue-900"></i> Paso 3: Previsualización de la Solicitud
                </h2>
            </div>

            <!-- Resumen de Datos del Cliente -->
            <div class="bg-slate-50 border border-slate-200 rounded-xl p-5 mb-6 text-xs">
                <div class="flex justify-between items-center mb-3 border-b border-slate-200 pb-2">
                    <span class="font-bold text-slate-900 text-sm">Empresa / Solicitante</span>
                    <button onclick="irAPaso(1)" class="text-blue-900 hover:underline font-bold flex items-center gap-1">
                        <i class="fa-solid fa-pen-to-square"></i> Modificar datos fiscales
                    </button>
                </div>
                <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
                    <div><span class="text-slate-500">Razón Social:</span> <strong id="prev-nombre" class="block text-slate-900 mt-0.5"></strong></div>
                    <div><span class="text-slate-500">RFC:</span> <strong id="prev-rfc" class="block text-slate-900 mt-0.5 uppercase"></strong></div>
                    <div><span class="text-slate-500">Representante:</span> <strong id="prev-rep" class="block text-slate-900 mt-0.5"></strong></div>
                    <div><span class="text-slate-500">Correo Electrónico:</span> <strong id="prev-correo" class="block text-slate-900 mt-0.5"></strong></div>
                    <div><span class="text-slate-500">Teléfono:</span> <strong id="prev-tel" class="block text-slate-900 mt-0.5"></strong></div>
                    <div><span class="text-slate-500">Régimen IVA:</span> <strong id="prev-iva" class="block text-slate-900 mt-0.5"></strong></div>
                </div>
            </div>

            <!-- Resumen de Equipos -->
            <div class="mb-6">
                <div class="flex justify-between items-center mb-3">
                    <span class="font-bold text-slate-900 text-sm">Equipos a Calibrar (<span id="prev-count-equipos">0</span> partidas)</span>
                    <button onclick="irAPaso(2)" class="text-blue-900 hover:underline font-bold text-xs flex items-center gap-1">
                        <i class="fa-solid fa-pen-to-square"></i> Modificar instrumentos
                    </button>
                </div>
                <div class="overflow-x-auto border border-slate-200 rounded-xl">
                    <table class="w-full text-left text-xs">
                        <thead class="bg-slate-100 text-slate-700 font-bold border-b border-slate-200">
                            <tr>
                                <th class="p-3 w-12 text-center">#</th>
                                <th class="p-3">Descripción del Instrumento</th>
                                <th class="p-3">Marca y Modelo</th>
                                <th class="p-3">No. de Serie</th>
                                <th class="p-3">Alcance / Intervalo</th>
                                <th class="p-3 text-center">Modalidad</th>
                            </tr>
                        </thead>
                        <tbody id="prev-tabla-instrumentos" class="divide-y divide-slate-200 bg-white"></tbody>
                    </table>
                </div>
            </div>

            <div class="mt-8 flex justify-between items-center pt-4 border-t border-slate-200">
                <button onclick="irAPaso(2)" class="bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold text-sm px-5 py-2.5 rounded-xl transition flex items-center gap-2">
                    <i class="fa-solid fa-arrow-left"></i> Regresar a Instrumentos
                </button>
                <button id="btn-confirmar-envio" onclick="confirmarYEnviarSolicitud()" class="bg-emerald-700 hover:bg-emerald-600 text-white font-bold text-sm px-7 py-3.5 rounded-xl shadow-lg transition flex items-center gap-2">
                    <i class="fa-solid fa-paper-plane"></i> Confirmar y Enviar Solicitud a CENAM
                </button>
            </div>
        </div>

        <!-- PASO 4: ACUSE OFICIAL DE RECEPCIÓN -->
        <div id="panel-step-4" class="hidden bg-white rounded-2xl shadow-md border border-slate-200 p-8 text-center">
            <div class="w-16 h-16 bg-emerald-100 text-emerald-700 rounded-full flex items-center justify-center text-3xl mx-auto mb-4">
                <i class="fa-solid fa-circle-check"></i>
            </div>
            <h2 class="text-2xl font-extrabold text-slate-900 mb-2">¡Solicitud Recibida Exitosamente!</h2>
            <p class="text-sm text-slate-600 max-w-lg mx-auto mb-6">
                Su requerimiento de calibración ha ingresado al sistema de Ventanilla de Servicios (SSI) de CENAM con los siguientes datos oficiales:
            </p>

            <div class="bg-gradient-to-r from-blue-900 to-slate-900 text-white p-6 rounded-2xl max-w-md mx-auto shadow-lg mb-6 text-left">
                <div class="flex justify-between items-center border-b border-blue-700/60 pb-3 mb-3">
                    <span class="text-xs text-blue-200 font-bold uppercase tracking-wider">Folio Oficial CENAM</span>
                    <span id="acuse-folio" class="text-2xl font-black text-amber-400 font-mono">----</span>
                </div>
                <div class="flex justify-between items-center text-xs mb-2">
                    <span class="text-slate-300">Clave de Seguimiento:</span>
                    <span id="acuse-token" class="font-mono font-bold text-white bg-slate-800 px-2 py-0.5 rounded">----</span>
                </div>
                <div class="flex justify-between items-center text-xs">
                    <span class="text-slate-300">Partidas Registradas:</span>
                    <span id="acuse-partidas" class="font-bold text-white">0</span>
                </div>
            </div>

            <div class="bg-blue-50 border border-blue-200 rounded-xl p-4 max-w-lg mx-auto text-xs text-blue-900 text-left mb-8">
                <p class="font-bold mb-1"><i class="fa-solid fa-clock-rotate-left mr-1"></i> Próximos Pasos Institucionales:</p>
                <ol class="list-decimal list-inside space-y-1 text-blue-800">
                    <li>Hemos enviado una copia del acuse a su correo electrónico.</li>
                    <li>Ventanilla SSI turnará las partidas a las Áreas Técnicas especializadas.</li>
                    <li>En un plazo máximo de <strong>3 días hábiles</strong> recibirá la cotización oficial formal para su aprobación.</li>
                </ol>
            </div>

            <div class="flex flex-col sm:flex-row justify-center gap-3">
                <a id="btn-ir-portal-directo" href="/portal" class="bg-blue-900 hover:bg-blue-800 text-white font-bold text-sm px-6 py-3 rounded-xl shadow transition flex items-center justify-center gap-2">
                    <i class="fa-solid fa-chart-line"></i> Ir a mi Portal de Seguimiento
                </a>
                <button onclick="window.print()" class="bg-slate-100 hover:bg-slate-200 text-slate-800 font-bold text-sm px-5 py-3 rounded-xl transition flex items-center justify-center gap-2">
                    <i class="fa-solid fa-print"></i> Imprimir Acuse
                </button>
            </div>
        </div>
    </main>

    <!-- Footer Institucional -->
    <footer class="bg-slate-900 text-slate-400 text-xs py-6 border-t border-slate-800 mt-8 text-center">
        <p>&copy; 2026 Centro Nacional de Metrología (CENAM) &bull; Km 4,5 Carretera a Los Cués, Mpio. El Marqués, C.P. 76246, Querétaro, México.</p>
        <p class="mt-1 text-[11px] text-slate-500">Sistema Certificado bajo ISO/IEC 17025 / ISO 9001</p>
    </footer>

    <script>
        let instrumentosList = [];

        function initForm() {
            agregarInstrumento();
        }

        function irAPaso(paso) {
            [1, 2, 3, 4].forEach(p => {
                document.getElementById(`panel-step-${p}`).classList.add('hidden');
                const b = document.getElementById(`badge-step-${p}`);
                if (p === paso) {
                    b.className = "w-9 h-9 rounded-full bg-blue-900 text-white font-bold flex items-center justify-center text-sm shadow ring-4 ring-white";
                } else if (p < paso) {
                    b.className = "w-9 h-9 rounded-full bg-emerald-600 text-white font-bold flex items-center justify-center text-sm shadow ring-4 ring-white";
                    b.innerHTML = '<i class="fa-solid fa-check"></i>';
                } else {
                    b.className = "w-9 h-9 rounded-full bg-slate-200 text-slate-600 font-bold flex items-center justify-center text-sm shadow ring-4 ring-white";
                    b.innerText = p;
                }
            });
            document.getElementById(`panel-step-${paso}`).classList.remove('hidden');

            const bar = document.getElementById('step-bar');
            if (paso === 1) bar.style.width = '0%';
            if (paso === 2) bar.style.width = '33%';
            if (paso === 3) bar.style.width = '66%';
            if (paso === 4) bar.style.width = '100%';

            window.scrollTo({ top: 0, behavior: 'smooth' });
        }

        function irAPaso2() {
            const nombre = document.getElementById('cli-nombre').value.trim();
            const rfc = document.getElementById('cli-rfc').value.trim();
            const rep = document.getElementById('cli-rep').value.trim();
            const correo = document.getElementById('cli-correo').value.trim();
            const tel = document.getElementById('cli-tel').value.trim();

            if (!nombre) { alert("Por favor ingrese el Nombre o Razón Social."); document.getElementById('cli-nombre').focus(); return; }
            if (!rfc || rfc.length < 10) { alert("Por favor ingrese un RFC válido."); document.getElementById('cli-rfc').focus(); return; }
            if (!rep) { alert("Por favor ingrese el Nombre del Contacto o Representante."); document.getElementById('cli-rep').focus(); return; }
            if (!correo || !correo.includes('@')) { alert("Por favor ingrese un Correo Electrónico válido."); document.getElementById('cli-correo').focus(); return; }
            if (!tel) { alert("Por favor ingrese un Teléfono de contacto."); document.getElementById('cli-tel').focus(); return; }

            irAPaso(2);
        }

        function agregarInstrumento() {
            const idx = instrumentosList.length;
            instrumentosList.push({
                desc: "",
                marca: "",
                modelo: "",
                serie: "",
                alcance: "",
                es_in_situ: 0
            });
            renderInstrumentos();
        }

        function eliminarInstrumento(idx) {
            if (instrumentosList.length <= 1) {
                alert("Debe incluir al menos un instrumento en su solicitud.");
                return;
            }
            instrumentosList.splice(idx, 1);
            renderInstrumentos();
        }

        function updateInst(idx, field, val) {
            instrumentosList[idx][field] = val;
        }

        function renderInstrumentos() {
            const container = document.getElementById('instrumentos-container');
            container.innerHTML = instrumentosList.map((inst, idx) => `
                <div class="border border-slate-200 bg-slate-50 rounded-xl p-4 sm:p-5 relative shadow-sm">
                    <div class="flex justify-between items-center pb-2 mb-3 border-b border-slate-200">
                        <span class="font-bold text-slate-800 text-sm flex items-center gap-1.5">
                            <span class="bg-blue-900 text-white w-5 h-5 rounded-full flex items-center justify-center text-xs">${idx + 1}</span>
                            Instrumento ${idx + 1}
                        </span>
                        ${instrumentosList.length > 1 ? `
                            <button onclick="eliminarInstrumento(${idx})" class="text-red-600 hover:text-red-800 text-xs font-bold flex items-center gap-1">
                                <i class="fa-solid fa-trash"></i> Eliminar
                            </button>
                        ` : ''}
                    </div>
                    <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
                        <div class="md:col-span-2">
                            <label class="block text-xs font-bold text-slate-700 mb-1">Descripción del Instrumento o Calibración *</label>
                            <input type="text" value="${inst.desc}" onchange="updateInst(${idx}, 'desc', this.value)" placeholder="Ej. Multímetro digital 6.5 dígitos, Termómetro de resistencia, Bloque patrón" class="w-full bg-white border border-slate-300 rounded-lg p-2 text-xs focus:ring-1 focus:ring-blue-900 outline-none">
                        </div>
                        <div>
                            <label class="block text-xs font-bold text-slate-700 mb-1">Intervalo / Alcance Requerido</label>
                            <input type="text" value="${inst.alcance}" onchange="updateInst(${idx}, 'alcance', this.value)" placeholder="Ej. 0 V a 1000 V / -50 °C a 200 °C" class="w-full bg-white border border-slate-300 rounded-lg p-2 text-xs">
                        </div>
                        <div>
                            <label class="block text-xs font-bold text-slate-700 mb-1">Marca</label>
                            <input type="text" value="${inst.marca}" onchange="updateInst(${idx}, 'marca', this.value)" placeholder="Ej. Fluke, Mitutoyo, Keysight" class="w-full bg-white border border-slate-300 rounded-lg p-2 text-xs">
                        </div>
                        <div>
                            <label class="block text-xs font-bold text-slate-700 mb-1">Modelo</label>
                            <input type="text" value="${inst.modelo}" onchange="updateInst(${idx}, 'modelo', this.value)" placeholder="Ej. 8846A, BM1-103" class="w-full bg-white border border-slate-300 rounded-lg p-2 text-xs">
                        </div>
                        <div>
                            <label class="block text-xs font-bold text-slate-700 mb-1">Número de Serie</label>
                            <input type="text" value="${inst.serie}" onchange="updateInst(${idx}, 'serie', this.value)" placeholder="Ej. SN-9821820" class="w-full bg-white border border-slate-300 rounded-lg p-2 text-xs">
                        </div>
                        <div class="md:col-span-3 pt-2">
                            <label class="inline-flex items-center cursor-pointer">
                                <input type="checkbox" ${inst.es_in_situ ? 'checked' : ''} onchange="updateInst(${idx}, 'es_in_situ', this.checked ? 1 : 0)" class="w-4 h-4 text-blue-900 rounded border-slate-300 focus:ring-blue-900">
                                <span class="ml-2 text-xs font-bold text-slate-800">¿Requiere calibración IN SITU (en sus propias instalaciones / planta)?</span>
                            </label>
                        </div>
                    </div>
                </div>
            `).join('');
        }

        function irAPaso3() {
            for (let i = 0; i < instrumentosList.length; i++) {
                if (!instrumentosList[i].desc.trim()) {
                    alert(`Por favor ingrese la descripción para el Instrumento ${i + 1}.`);
                    return;
                }
            }

            // Llenar vista previa
            document.getElementById('prev-nombre').innerText = document.getElementById('cli-nombre').value.trim();
            document.getElementById('prev-rfc').innerText = document.getElementById('cli-rfc').value.trim();
            document.getElementById('prev-rep').innerText = document.getElementById('cli-rep').value.trim();
            document.getElementById('prev-correo').innerText = document.getElementById('cli-correo').value.trim();
            document.getElementById('prev-tel').innerText = document.getElementById('cli-tel').value.trim();
            document.getElementById('prev-iva').innerText = document.getElementById('cli-iva').checked ? "Aplica 16% I.V.A." : "Tasa Cero / Extranjero";
            document.getElementById('prev-count-equipos').innerText = instrumentosList.length;

            const tbody = document.getElementById('prev-tabla-instrumentos');
            tbody.innerHTML = instrumentosList.map((inst, idx) => `
                <tr class="hover:bg-slate-50">
                    <td class="p-3 text-center font-bold text-slate-700">${idx + 1}</td>
                    <td class="p-3 font-semibold text-slate-900">${inst.desc}</td>
                    <td class="p-3 text-slate-600">${inst.marca || '-'} ${inst.modelo ? `/ ${inst.modelo}` : ''}</td>
                    <td class="p-3 text-slate-600 font-mono">${inst.serie || 'S/N'}</td>
                    <td class="p-3 text-slate-600">${inst.alcance || '-'}</td>
                    <td class="p-3 text-center">
                        <span class="px-2 py-0.5 rounded text-[10px] font-bold ${inst.es_in_situ ? 'bg-amber-100 text-amber-800' : 'bg-blue-100 text-blue-800'}">
                            ${inst.es_in_situ ? 'IN SITU' : 'LAB CENAM'}
                        </span>
                    </td>
                </tr>
            `).join('');

            irAPaso(3);
        }

        async function confirmarYEnviarSolicitud() {
            const btn = document.getElementById('btn-confirmar-envio');
            btn.disabled = true;
            btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin mr-2"></i> Generando Folio y Registrando...';

            const payload = {
                cliente: {
                    cliente: document.getElementById('cli-nombre').value.trim(),
                    rfc: document.getElementById('cli-rfc').value.trim(),
                    representante: document.getElementById('cli-rep').value.trim(),
                    correo: document.getElementById('cli-correo').value.trim(),
                    telefono: document.getElementById('cli-tel').value.trim(),
                    pais: document.getElementById('cli-pais').value.trim() || 'México',
                    direccion: document.getElementById('cli-dir').value.trim(),
                    aplica_iva: document.getElementById('cli-iva').checked ? 1 : 0
                },
                instrumentos: instrumentosList
            };

            try {
                const res = await fetch('/api/public/solicitudes/crear', {
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

                if (res.ok && data.status === 'success') {
                    document.getElementById('acuse-folio').innerText = data.data.no_folio;
                    document.getElementById('acuse-token').innerText = data.data.token_seguimiento;
                    document.getElementById('acuse-partidas').innerText = instrumentosList.length;
                    document.getElementById('btn-ir-portal-directo').href = `/portal?folio=${data.data.no_folio}&token=${data.data.token_seguimiento}`;
                    irAPaso(4);
                } else {
                    alert(`Error al registrar solicitud: ${data.detail || 'Ocurrió un error inesperado'}`);
                    btn.disabled = false;
                    btn.innerHTML = '<i class="fa-solid fa-paper-plane mr-2"></i> Confirmar y Enviar Solicitud a CENAM';
                }
            } catch (err) {
                alert(`Error de red: ${err.message}`);
                btn.disabled = false;
                btn.innerHTML = '<i class="fa-solid fa-paper-plane mr-2"></i> Confirmar y Enviar Solicitud a CENAM';
            }
        }

        window.onload = initForm;
    </script>
</body>
</html>
"""

PORTAL_CLIENTE_HTML = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CENAM - Portal de Clientes y Seguimiento</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        :root { --cenam-navy: #1e3a8a; --cenam-gold: #8a6d3b; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f1f5f9; color: #1e293b; }
        .hidden { display: none !important; }
    </style>
</head>
<body class="min-h-screen flex flex-col justify-between">
    <!-- Header -->
    <header class="bg-slate-900 text-white shadow-md border-b-4 border-amber-600">
        <div class="max-w-6xl mx-auto px-4 py-4 flex flex-col sm:flex-row justify-between items-center gap-3">
            <div class="flex items-center space-x-3">
                <div class="w-10 h-10 rounded-lg bg-amber-600 flex items-center justify-center font-bold text-white text-xl shadow">
                    <i class="fa-solid fa-user-shield"></i>
                </div>
                <div>
                    <h1 class="text-base sm:text-lg font-extrabold tracking-tight">PORTAL DE CLIENTES CENAM</h1>
                    <p class="text-xs text-slate-300">Consulta de Solicitudes, Cotizaciones y Aprobación de Fechas</p>
                </div>
            </div>
            <div id="header-user-info" class="hidden flex items-center gap-3 text-xs">
                <span class="bg-slate-800 px-3 py-1.5 rounded-lg border border-slate-700 text-slate-300">
                    <i class="fa-solid fa-envelope text-amber-400 mr-1.5"></i> <strong id="logged-user-email"></strong>
                </span>
                <button onclick="cerrarSesionCliente()" class="bg-red-900/40 hover:bg-red-800 text-red-200 px-3 py-1.5 rounded-lg border border-red-700/50 transition">
                    <i class="fa-solid fa-right-from-bracket mr-1"></i> Salir
                </button>
            </div>
        </div>
    </header>

    <!-- Main Content -->
    <main class="max-w-6xl mx-auto w-full px-4 py-8 flex-1">
        <!-- VISTA 1: LOGIN SENCILLO Y EFECTIVO -->
        <div id="view-login" class="max-w-md mx-auto bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
            <!-- Tabs del Login -->
            <div class="flex border-b border-slate-200 bg-slate-50 text-xs font-bold text-slate-600">
                <button id="tab-btn-otp" onclick="switchLoginTab('otp')" class="flex-1 py-3.5 border-b-2 border-blue-900 text-blue-900 bg-white flex items-center justify-center gap-1.5">
                    <i class="fa-solid fa-key"></i> Código al Correo (OTP)
                </button>
                <button id="tab-btn-folio" onclick="switchLoginTab('folio')" class="flex-1 py-3.5 border-b-2 border-transparent hover:text-slate-900 flex items-center justify-center gap-1.5">
                    <i class="fa-solid fa-ticket"></i> Consulta por Folio
                </button>
            </div>

            <!-- Panel Login por OTP -->
            <div id="panel-login-otp" class="p-6">
                <div class="mb-4 text-center">
                    <div class="w-12 h-12 rounded-full bg-blue-50 text-blue-900 flex items-center justify-center text-xl mx-auto mb-2">
                        <i class="fa-solid fa-shield-halved"></i>
                    </div>
                    <h3 class="font-bold text-slate-900 text-base">Acceso Seguro sin Contraseña</h3>
                    <p class="text-xs text-slate-500 mt-0.5">Le enviaremos un código de 6 dígitos válido por 10 minutos.</p>
                </div>

                <!-- Sub-Paso A: Solicitar Correo -->
                <div id="otp-step-request">
                    <label class="block text-xs font-bold text-slate-700 mb-1">Correo Electrónico de la Empresa</label>
                    <input type="email" id="login-email" placeholder="contacto@empresa.com" onkeydown="if(event.key==='Enter') solicitarCodigoOTP()" class="w-full bg-slate-50 border border-slate-300 rounded-lg p-2.5 text-sm focus:ring-2 focus:ring-blue-900 focus:bg-white outline-none mb-4">
                    <button id="btn-solicitar-otp" onclick="solicitarCodigoOTP()" class="w-full bg-blue-900 hover:bg-blue-800 text-white font-bold text-sm py-3 rounded-xl shadow transition flex items-center justify-center gap-2">
                        <i class="fa-solid fa-paper-plane"></i> Solicitar Código de 6 Dígitos
                    </button>
                </div>

                <!-- Sub-Paso B: Ingresar Código -->
                <div id="otp-step-verify" class="hidden">
                    <div class="bg-blue-50 border border-blue-200 rounded-lg p-3 text-xs text-blue-900 mb-4 flex justify-between items-center">
                        <span>Código enviado a: <strong id="sent-to-email"></strong></span>
                        <button onclick="cambiarEmailOTP()" class="text-blue-900 underline font-bold">Cambiar</button>
                    </div>

                    <!-- Notificación de código para pruebas / acceso rápido -->
                    <div id="dev-otp-banner" class="hidden bg-amber-50 border border-amber-300 text-amber-900 p-2.5 rounded-lg text-xs mb-3 font-semibold text-center">
                        <i class="fa-solid fa-key text-amber-700 mr-1"></i> Código de Verificación: <strong id="dev-otp-code" class="text-base font-mono text-amber-950 px-2 py-0.5 bg-amber-200 rounded tracking-wider"></strong>
                        <div class="text-[11px] font-normal text-amber-800 mt-1">También despachado a su bandeja de correo.</div>
                    </div>

                    <label class="block text-xs font-bold text-slate-700 mb-1 text-center">Ingrese el Código de 6 Dígitos</label>
                    <input type="text" id="login-otp-code" maxlength="6" placeholder="000000" onkeydown="if(event.key==='Enter') verificarCodigoOTP()" class="w-full text-center tracking-[8px] font-mono font-bold text-2xl bg-slate-50 border border-slate-300 rounded-lg p-2.5 focus:ring-2 focus:ring-blue-900 focus:bg-white outline-none mb-4">
                    
                    <button id="btn-verificar-otp" onclick="verificarCodigoOTP()" class="w-full bg-emerald-700 hover:bg-emerald-600 text-white font-bold text-sm py-3 rounded-xl shadow transition flex items-center justify-center gap-2 mb-2">
                        <i class="fa-solid fa-arrow-right-to-bracket"></i> Ingresar a mi Portal
                    </button>
                    <button onclick="solicitarCodigoOTP()" class="w-full text-center text-xs text-slate-500 hover:text-slate-800 py-1">
                        ¿No recibió el código? Reenviar
                    </button>
                </div>
            </div>

            <!-- Panel Login por Folio Directo -->
            <div id="panel-login-folio" class="hidden p-6">
                <div class="mb-4 text-center">
                    <h3 class="font-bold text-slate-900 text-base">Consulta Rápida de Folio</h3>
                    <p class="text-xs text-slate-500 mt-0.5">Ingrese el número de folio y la clave de seguimiento recibida en su acuse.</p>
                </div>

                <div class="space-y-3 mb-4">
                    <div>
                        <label class="block text-xs font-bold text-slate-700 mb-1">Número de Folio</label>
                        <input type="text" id="login-folio" placeholder="Ej. 0001-2026PR" class="w-full bg-slate-50 border border-slate-300 rounded-lg p-2.5 text-sm uppercase font-mono focus:ring-2 focus:ring-blue-900 focus:bg-white outline-none">
                    </div>
                    <div>
                        <label class="block text-xs font-bold text-slate-700 mb-1">Clave de Seguimiento (Token)</label>
                        <input type="text" id="login-token" placeholder="Ej. A1B2C3D4E5F6" class="w-full bg-slate-50 border border-slate-300 rounded-lg p-2.5 text-sm uppercase font-mono focus:ring-2 focus:ring-blue-900 focus:bg-white outline-none">
                    </div>
                </div>

                <button onclick="consultarPorFolioYToken()" class="w-full bg-blue-900 hover:bg-blue-800 text-white font-bold text-sm py-3 rounded-xl shadow transition flex items-center justify-center gap-2">
                    <i class="fa-solid fa-magnifying-glass"></i> Consultar Expediente
                </button>
            </div>
            
            <div class="bg-slate-50 border-t border-slate-200 p-4 text-center text-xs text-slate-500">
                ¿Aún no tiene un folio? <a href="/solicitud" class="text-blue-900 font-bold hover:underline">Capture una nueva solicitud aquí</a>.
            </div>
        </div>

        <!-- VISTA 2: TABLERO DEL CLIENTE (AUTENTICADO) -->
        <div id="view-dashboard" class="hidden">
            <!-- Barra superior del cliente -->
            <div class="bg-white rounded-2xl shadow-sm border border-slate-200 p-6 mb-6 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                <div>
                    <span class="text-xs font-bold text-blue-900 uppercase tracking-wider">Tablero Corporativo</span>
                    <h2 class="text-xl font-extrabold text-slate-900 mt-0.5" id="dash-cliente-nombre">Mis Solicitudes y Cotizaciones</h2>
                    <p class="text-xs text-slate-500">Consulte el avance metrológico, cotizaciones oficiales y programe la recepción de sus patrones.</p>
                </div>
                <div class="flex items-center gap-2">
                    <a href="/solicitud" class="bg-amber-600 hover:bg-amber-500 text-white font-bold text-xs px-4 py-2.5 rounded-xl shadow-sm transition flex items-center gap-1.5">
                        <i class="fa-solid fa-plus"></i> Nueva Solicitud
                    </a>
                    <button onclick="cargarExpedientesCliente()" class="bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold text-xs px-3 py-2.5 rounded-xl transition">
                        <i class="fa-solid fa-rotate"></i>
                    </button>
                </div>
            </div>

            <!-- Contenedor de Expedientes / Folios -->
            <div id="folios-container" class="space-y-6"></div>
        </div>
    </main>

    <!-- MODAL DE FORMALIZACIÓN Y ACEPTACIÓN DE COTIZACIÓN -->
    <div id="modal-aceptar-cotizacion" class="hidden fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
        <div class="bg-white rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto shadow-2xl border border-slate-200 p-6 sm:p-8">
            <div class="flex justify-between items-center border-b border-slate-200 pb-3 mb-4">
                <div>
                    <h3 class="text-lg font-bold text-slate-900 flex items-center gap-2">
                        <i class="fa-solid fa-file-signature text-emerald-700"></i> Aceptación Oficial de Cotización
                    </h3>
                    <p class="text-xs text-slate-500">Folio: <strong id="modal-folio-id" class="text-slate-900 font-mono"></strong></p>
                </div>
                <button onclick="cerrarModalAceptacion()" class="text-slate-400 hover:text-slate-700 text-lg">
                    <i class="fa-solid fa-xmark"></i>
                </button>
            </div>

            <p class="text-xs text-slate-600 mb-4">
                Seleccione las partidas que aprueba para calibración e ingrese su Orden de Compra (OC) o Pedido oficial para autorizar el turnado a programación de fechas en los laboratorios de CENAM:
            </p>

            <!-- Selección de Partidas -->
            <div class="border border-slate-200 rounded-xl overflow-hidden mb-5">
                <div class="bg-slate-100 px-4 py-2 text-xs font-bold text-slate-700 border-b border-slate-200 flex justify-between">
                    <span>Partidas Disponibles</span>
                    <span class="text-slate-500 font-normal">Marque las partidas a calibrar</span>
                </div>
                <div id="modal-partidas-list" class="divide-y divide-slate-200 text-xs p-2 max-h-48 overflow-y-auto"></div>
            </div>

            <div class="space-y-4 mb-6">
                <div>
                    <label class="block text-xs font-bold text-slate-700 mb-1">No. de Orden de Compra (OC) o Pedido Oficial *</label>
                    <input type="text" id="modal-no-oc" placeholder="Ej. OC-2026-88910 / PED-9921" class="w-full bg-slate-50 border border-slate-300 rounded-lg p-2.5 text-sm focus:ring-2 focus:ring-emerald-700 outline-none">
                </div>
                <div>
                    <label class="block text-xs font-bold text-slate-700 mb-1">Adjuntar Archivo de Orden de Compra (PDF opcional)</label>
                    <input type="file" id="modal-pdf-oc" accept=".pdf" class="w-full text-xs text-slate-600 file:mr-3 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-xs file:font-bold file:bg-blue-50 file:text-blue-900 hover:file:bg-blue-100 cursor-pointer">
                </div>
                <div class="bg-slate-50 p-3 rounded-lg border border-slate-200">
                    <label class="inline-flex items-start cursor-pointer text-xs">
                        <input type="checkbox" id="modal-check-terminos" class="w-4 h-4 text-emerald-700 rounded border-slate-300 mt-0.5">
                        <span class="ml-2 text-slate-700">Confirmo la aprobación de las partidas seleccionadas y autorizo a CENAM a programar los días de servicio conforme a los tiempos y costos estipulados.</span>
                    </label>
                </div>
            </div>

            <div class="flex justify-end gap-3 pt-3 border-t border-slate-200">
                <button onclick="cerrarModalAceptacion()" class="bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold text-xs px-4 py-2.5 rounded-lg transition">Cancelar</button>
                <button id="btn-confirmar-aceptacion" onclick="enviarAceptacionCotizacion()" class="bg-emerald-700 hover:bg-emerald-600 text-white font-bold text-xs px-6 py-2.5 rounded-lg shadow transition flex items-center gap-1.5">
                    <i class="fa-solid fa-check"></i> Formalizar Aceptación
                </button>
            </div>
        </div>
    </div>

    <!-- Footer -->
    <footer class="bg-slate-900 text-slate-400 text-xs py-6 border-t border-slate-800 mt-8 text-center">
        <p>&copy; 2026 Centro Nacional de Metrología (CENAM) &bull; Km 4,5 Carretera a Los Cués, Mpio. El Marqués, Querétaro, México.</p>
    </footer>

    <script>
        let currentAuthCorreo = "";
        let currentAuthToken = "";
        let currentFolioEnAceptacion = "";
        let expedientesCache = [];

        function switchLoginTab(tab) {
            if (tab === 'otp') {
                document.getElementById('panel-login-otp').classList.remove('hidden');
                document.getElementById('panel-login-folio').classList.add('hidden');
                document.getElementById('tab-btn-otp').className = "flex-1 py-3.5 border-b-2 border-blue-900 text-blue-900 bg-white flex items-center justify-center gap-1.5";
                document.getElementById('tab-btn-folio').className = "flex-1 py-3.5 border-b-2 border-transparent hover:text-slate-900 flex items-center justify-center gap-1.5";
            } else {
                document.getElementById('panel-login-otp').classList.add('hidden');
                document.getElementById('panel-login-folio').classList.remove('hidden');
                document.getElementById('tab-btn-otp').className = "flex-1 py-3.5 border-b-2 border-transparent hover:text-slate-900 flex items-center justify-center gap-1.5";
                document.getElementById('tab-btn-folio').className = "flex-1 py-3.5 border-b-2 border-blue-900 text-blue-900 bg-white flex items-center justify-center gap-1.5";
            }
        }

        async function solicitarCodigoOTP() {
            const email = document.getElementById('login-email').value.trim();
            if (!email || !email.includes('@')) {
                alert("Por favor ingrese un correo electrónico corporativo válido.");
                return;
            }

            const btn = document.getElementById('btn-solicitar-otp');
            btn.disabled = true;
            btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin mr-1.5"></i> Enviando código...';

            try {
                const res = await fetch('/api/public/auth/solicitar-otp', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ correo: email })
                });
                const data = await res.json();
                if (res.ok && data.status === 'success') {
                    currentAuthCorreo = email;
                    document.getElementById('sent-to-email').innerText = email;
                    document.getElementById('otp-step-request').classList.add('hidden');
                    document.getElementById('otp-step-verify').classList.remove('hidden');

                    if (data.dev_otp) {
                        document.getElementById('dev-otp-banner').classList.remove('hidden');
                        document.getElementById('dev-otp-code').innerText = data.dev_otp;
                    }
                    setTimeout(() => {
                        const codeInput = document.getElementById('login-otp-code');
                        if (codeInput) codeInput.focus();
                    }, 150);
                } else {
                    alert(`Error: ${data.detail || 'No se pudo enviar el código'}`);
                }
            } catch (err) {
                alert(`Error de red: ${err.message}`);
            } finally {
                btn.disabled = false;
                btn.innerHTML = '<i class="fa-solid fa-paper-plane mr-2"></i> Solicitar Código de 6 Dígitos';
            }
        }

        function cambiarEmailOTP() {
            document.getElementById('otp-step-request').classList.remove('hidden');
            document.getElementById('otp-step-verify').classList.add('hidden');
            document.getElementById('dev-otp-banner').classList.add('hidden');
        }

        async function verificarCodigoOTP() {
            const codigo = document.getElementById('login-otp-code').value.trim();
            if (!codigo || codigo.length !== 6) {
                alert("Por favor ingrese el código de 6 dígitos.");
                return;
            }

            const btn = document.getElementById('btn-verificar-otp');
            btn.disabled = true;
            btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin mr-1.5"></i> Verificando...';

            try {
                const res = await fetch('/api/public/auth/verificar-otp', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ correo: currentAuthCorreo, codigo: codigo })
                });
                const data = await res.json();
                if (res.ok && data.status === 'success') {
                    localStorage.setItem('cenam_cliente_email', currentAuthCorreo);
                    mostrarDashboard(currentAuthCorreo);
                } else {
                    alert(`Código inválido o expirado. Verifique e intente nuevamente.`);
                }
            } catch (err) {
                alert(`Error de red: ${err.message}`);
            } finally {
                btn.disabled = false;
                btn.innerHTML = '<i class="fa-solid fa-arrow-right-to-bracket mr-2"></i> Ingresar a mi Portal';
            }
        }

        async function consultarPorFolioYToken() {
            const folio = document.getElementById('login-folio').value.trim();
            const token = document.getElementById('login-token').value.trim();
            if (!folio) { alert("Por favor ingrese su número de Folio."); return; }
            if (!token) { alert("Por favor ingrese la Clave de Seguimiento (Token)."); return; }

            try {
                const res = await fetch(`/api/public/solicitudes/consultar?folio=${encodeURIComponent(folio)}&token=${encodeURIComponent(token)}`);
                const data = await res.json();
                if (res.ok && data.length > 0) {
                    currentAuthToken = token;
                    mostrarDashboard(null, data);
                } else {
                    alert("No se encontró ningún expediente con ese Folio y Clave de Seguimiento.");
                }
            } catch (err) {
                alert(`Error de red: ${err.message}`);
            }
        }

        function mostrarDashboard(correo, foliosData = null) {
            document.getElementById('view-login').classList.add('hidden');
            document.getElementById('view-dashboard').classList.remove('hidden');
            document.getElementById('header-user-info').classList.remove('hidden');
            document.getElementById('logged-user-email').innerText = correo || (foliosData ? foliosData[0].cliente : "Cliente");

            if (foliosData) {
                expedientesCache = foliosData;
                renderExpedientes();
            } else {
                cargarExpedientesCliente();
            }
        }

        async function cargarExpedientesCliente() {
            const email = currentAuthCorreo || localStorage.getItem('cenam_cliente_email');
            if (!email) return;

            const container = document.getElementById('folios-container');
            container.innerHTML = '<div class="text-center py-12 text-slate-500"><i class="fa-solid fa-spinner fa-spin text-2xl mb-2"></i><p class="text-xs">Cargando sus solicitudes oficiales...</p></div>';

            try {
                const res = await fetch(`/api/public/solicitudes/consultar?correo=${encodeURIComponent(email)}`);
                const data = await res.json();
                expedientesCache = data;
                renderExpedientes();
            } catch (err) {
                container.innerHTML = `<div class="bg-red-50 text-red-700 p-4 rounded-xl text-center text-xs font-bold">Error al cargar solicitudes: ${err.message}</div>`;
            }
        }

        function renderExpedientes() {
            const container = document.getElementById('folios-container');
            if (!expedientesCache || expedientesCache.length === 0) {
                container.innerHTML = `
                    <div class="bg-white rounded-2xl p-12 text-center border border-slate-200">
                        <i class="fa-regular fa-folder-open text-4xl text-slate-300 mb-3"></i>
                        <h3 class="font-bold text-slate-800 text-sm">No hay solicitudes registradas con este acceso</h3>
                        <p class="text-xs text-slate-500 mt-1 mb-4">Puede registrar su primera solicitud de calibración en minutos.</p>
                        <a href="/solicitud" class="bg-blue-900 hover:bg-blue-800 text-white font-bold text-xs px-5 py-2.5 rounded-lg transition">Capturar Solicitud</a>
                    </div>
                `;
                return;
            }

            container.innerHTML = expedientesCache.map(f => {
                const badgeClass = f.estado_general === 'ACEPTADA_CLIENTE' ? 'bg-emerald-100 text-emerald-800 border-emerald-300' :
                                   f.estado_general === 'COTIZADA' ? 'bg-blue-100 text-blue-900 border-blue-300' :
                                   'bg-amber-100 text-amber-900 border-amber-300';
                
                const estadoTexto = f.estado_general === 'ACEPTADA_CLIENTE' ? 'ACEPTADA POR CLIENTE' :
                                    f.estado_general === 'COTIZADA' ? 'COTIZACIÓN DISPONIBLE' :
                                    f.estado_general === 'TURNADA' ? 'EN REVISIÓN TÉCNICA' : f.estado_general;

                return `
                <div class="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
                    <!-- Cabecera del Folio -->
                    <div class="p-6 border-b border-slate-200 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 bg-slate-50">
                        <div>
                            <div class="flex items-center gap-2 mb-1">
                                <span class="font-mono font-extrabold text-base sm:text-lg text-slate-900">Folio: ${f.no_folio}</span>
                                <span class="px-2.5 py-0.5 rounded-full text-[11px] font-bold border ${badgeClass}">${estadoTexto}</span>
                            </div>
                            <p class="text-xs text-slate-500">
                                Fecha de recepción: ${f.fecha_recepcion} &bull; Contacto: ${f.cliente}
                            </p>
                        </div>
                        <div class="text-right">
                            ${f.tiene_cotizacion ? `
                                <span class="text-xs text-slate-500 block">Cotización Oficial: <strong class="text-slate-900 font-mono">${f.no_cotizacion}</strong></span>
                                <span class="text-sm font-black text-blue-900">$${f.total.toLocaleString('es-MX', {minimumFractionDigits: 2})} MXN</span>
                            ` : `
                                <span class="text-xs text-amber-800 font-bold bg-amber-50 px-3 py-1.5 rounded-lg border border-amber-200">
                                    <i class="fa-solid fa-clock"></i> Cotización en proceso
                                </span>
                            `}
                        </div>
                    </div>

                    <!-- Tabla de Partidas del Folio -->
                    <div class="p-6">
                        <h4 class="text-xs font-bold text-slate-700 uppercase tracking-wider mb-3">Partidas e Instrumentos Solicitados</h4>
                        <div class="overflow-x-auto border border-slate-200 rounded-xl mb-4">
                            <table class="w-full text-left text-xs">
                                <thead class="bg-slate-100 text-slate-700 font-bold border-b border-slate-200">
                                    <tr>
                                        <th class="p-3 w-10 text-center">#</th>
                                        <th class="p-3">Instrumento</th>
                                        <th class="p-3">Marca / Modelo / Serie</th>
                                        <th class="p-3">Servicio Metrológico</th>
                                        <th class="p-3 text-right">Costo Unitario</th>
                                        <th class="p-3 text-center">Fechas Programadas</th>
                                    </tr>
                                </thead>
                                <tbody class="divide-y divide-slate-200">
                                    ${f.partidas.map(p => `
                                        <tr class="hover:bg-slate-50">
                                            <td class="p-3 text-center font-bold text-slate-600">${p.numero_partida}</td>
                                            <td class="p-3 font-semibold text-slate-900">${p.descripcion_equipo}</td>
                                            <td class="p-3 text-slate-600">${p.marca || ''} ${p.modelo ? `/ ${p.modelo}` : ''} <span class="font-mono text-[11px] block text-slate-500">SN: ${p.no_serie || 'S/N'}</span></td>
                                            <td class="p-3 text-slate-700">${p.descripcion_servicio || 'Por asignar por Área Técnica'}</td>
                                            <td class="p-3 text-right font-mono font-bold text-slate-900">
                                                ${p.precio_total > 0 ? `$${parseFloat(p.precio_total).toLocaleString('es-MX', {minimumFractionDigits: 2})}` : '<span class="text-slate-400">En revisión</span>'}
                                            </td>
                                            <td class="p-3 text-center text-[11px]">
                                                ${p.fecha_recepcion_prog ? `
                                                    <span class="bg-blue-50 text-blue-900 font-semibold px-2 py-0.5 rounded block">Recepción: ${p.fecha_recepcion_prog}</span>
                                                    <span class="text-slate-500 block text-[10px] mt-0.5">Entrega: ${p.fecha_entrega_prog || '-'}</span>
                                                ` : '<span class="text-slate-400">Pendiente</span>'}
                                            </td>
                                        </tr>
                                    `).join('')}
                                </tbody>
                            </table>
                        </div>

                        <!-- Panel de Acción: Si está cotizada, mostrar botón de Aceptación -->
                        <div class="bg-slate-50 border border-slate-200 rounded-xl p-4 flex flex-col sm:flex-row justify-between items-center gap-3">
                            <div>
                                ${f.estado_general === 'ACEPTADA_CLIENTE' ? `
                                    <span class="text-xs font-bold text-emerald-800 flex items-center gap-1.5">
                                        <i class="fa-solid fa-circle-check text-emerald-600"></i> Aceptada con No. Orden de Compra: <strong>${f.no_orden_compra || 'Registrada'}</strong>
                                    </span>
                                    <span class="text-[11px] text-slate-500 block mt-0.5">Fecha de aceptación: ${f.fecha_aceptacion_cliente || '-'}</span>
                                ` : f.tiene_cotizacion ? `
                                    <span class="text-xs font-bold text-blue-900">Cotización Vigente hasta: ${f.vigencia_cot || '30 días'}</span>
                                    <span class="text-[11px] text-slate-500 block">Revise los costos y formalice su aceptación con su Orden de Compra.</span>
                                ` : `
                                    <span class="text-xs text-slate-600">Ventanilla SSI y los laboratorios están procesando el expediente.</span>
                                `}
                            </div>
                            <div class="flex items-center gap-2">
                                ${f.tiene_cotizacion && f.estado_general !== 'ACEPTADA_CLIENTE' ? `
                                    <button onclick="abrirModalAceptacion('${f.no_folio}')" class="bg-emerald-700 hover:bg-emerald-600 text-white font-bold text-xs px-5 py-2.5 rounded-xl shadow-md transition flex items-center gap-1.5">
                                        <i class="fa-solid fa-signature"></i> Aceptar Cotización (Orden de Compra)
                                    </button>
                                ` : ''}
                            </div>
                        </div>
                    </div>
                </div>
                `;
            }).join('');
        }

        function abrirModalAceptacion(folio) {
            currentFolioEnAceptacion = folio;
            const exp = expedientesCache.find(e => e.no_folio === folio);
            if (!exp) return;

            document.getElementById('modal-folio-id').innerText = folio;
            document.getElementById('modal-no-oc').value = exp.no_orden_compra || '';
            document.getElementById('modal-check-terminos').checked = false;

            const container = document.getElementById('modal-partidas-list');
            container.innerHTML = exp.partidas.map(p => `
                <div class="flex items-center justify-between p-2 hover:bg-slate-50">
                    <label class="flex items-center gap-2 cursor-pointer flex-1">
                        <input type="checkbox" name="partida_check" value="${p.id}" checked class="w-4 h-4 text-emerald-700 rounded border-slate-300">
                        <span><strong>Partida ${p.numero_partida}:</strong> ${p.descripcion_equipo} (${p.marca || ''} ${p.modelo || ''})</span>
                    </label>
                    <span class="font-mono font-bold text-slate-800 ml-3">$${parseFloat(p.precio_total || 0).toLocaleString('es-MX', {minimumFractionDigits: 2})}</span>
                </div>
            `).join('');

            document.getElementById('modal-aceptar-cotizacion').classList.remove('hidden');
        }

        function cerrarModalAceptacion() {
            document.getElementById('modal-aceptar-cotizacion').classList.add('hidden');
        }

        async function enviarAceptacionCotizacion() {
            const noOC = document.getElementById('modal-no-oc').value.trim();
            const terminos = document.getElementById('modal-check-terminos').checked;

            if (!noOC) {
                alert("Por favor ingrese el Número de Orden de Compra o Pedido Oficial.");
                document.getElementById('modal-no-oc').focus();
                return;
            }
            if (!terminos) {
                alert("Debe confirmar la aceptación de términos para continuar.");
                return;
            }

            const checkboxes = document.querySelectorAll('input[name="partida_check"]:checked');
            const partidasAceptadas = Array.from(checkboxes).map(c => parseInt(c.value));
            if (partidasAceptadas.length === 0) {
                alert("Debe seleccionar al menos una partida para aceptar.");
                return;
            }

            const btn = document.getElementById('btn-confirmar-aceptacion');
            btn.disabled = true;
            btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin mr-1.5"></i> Procesando...';

            const payload = {
                no_folio: currentFolioEnAceptacion,
                no_orden_compra: noOC,
                partidas_aceptadas: partidasAceptadas,
                correo: currentAuthCorreo || localStorage.getItem('cenam_cliente_email'),
                token: currentAuthToken
            };

            try {
                const res = await fetch('/api/public/solicitudes/aceptar-cotizacion', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                const data = await res.json();
                if (res.ok && data.status === 'success') {
                    alert("🎉 ¡Cotización Aceptada Oficialmente!\\n\\nSe ha notificado a Ventanilla SSI y a los laboratorios de CENAM para la asignación definitiva de fechas de calibración.");
                    cerrarModalAceptacion();
                    cargarExpedientesCliente();
                } else {
                    alert(`Error: ${data.detail || 'No se pudo registrar la aceptación'}`);
                }
            } catch (err) {
                alert(`Error de red: ${err.message}`);
            } finally {
                btn.disabled = false;
                btn.innerHTML = '<i class="fa-solid fa-check"></i> Formalizar Aceptación';
            }
        }

        function cerrarSesionCliente() {
            localStorage.removeItem('cenam_cliente_email');
            currentAuthCorreo = "";
            currentAuthToken = "";
            location.href = "/portal";
        }

        // Revisar si viene token y folio en la URL
        window.onload = function() {
            const params = new URLSearchParams(window.location.search);
            const folio = params.get('folio');
            const token = params.get('token');

            if (folio && token) {
                document.getElementById('login-folio').value = folio;
                document.getElementById('login-token').value = token;
                consultarPorFolioYToken();
            } else {
                const savedEmail = localStorage.getItem('cenam_cliente_email');
                if (savedEmail) {
                    currentAuthCorreo = savedEmail;
                    mostrarDashboard(savedEmail);
                }
            }
        };
    </script>
</body>
</html>
"""
