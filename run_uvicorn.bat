@echo off
title Sistema CENAM - Servidor Uvicorn ASGI
echo ========================================================
echo  Iniciando Servidor ASGI de Alto Rendimiento (Uvicorn)
echo  Plataforma: CENAM - Cotizaciones y Calibraciones (SCS)
echo.
echo  Interfaz Web:        http://localhost:8000
echo  Documentacion API:   http://localhost:8000/docs
echo ========================================================
echo.

python -m uvicorn server:app --host 0.0.0.0 --port 8000 --reload

pause
