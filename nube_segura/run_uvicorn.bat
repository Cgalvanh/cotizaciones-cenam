@echo off
title Sistema CENAM - Nube Segura (Servidor Uvicorn)
echo ========================================================
echo  Iniciando Servidor Uvicorn (Nube Segura / Supabase)
echo  Plataforma: CENAM Cloud Run
echo.
echo  Interfaz Web:        http://localhost:8080
echo  Documentacion API:   http://localhost:8080/docs
echo ========================================================
echo.

cd /d "%~dp0"
python -m uvicorn server:app --host 0.0.0.0 --port 8080 --reload

pause
