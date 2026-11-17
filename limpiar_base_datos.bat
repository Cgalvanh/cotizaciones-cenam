@echo off
chcp 65001 > nul
echo ========================================================
echo       CENAM - LIMPIEZA DE BASE DE DATOS DE PRUEBA
echo ========================================================
echo.
echo Esta herramienta eliminará las solicitudes y partidas de prueba,
echo dejando los catálogos y usuarios intactos para empezar en limpio.
echo.
set /p CONFIRMA="¿Desea limpiar las solicitudes de prueba? (S/N): "
if /i "%CONFIRMA%"=="S" (
    C:\Python314\python.exe scripts\limpiar_bd.py --modo ambas --limpiar-pdfs
    echo.
    echo Proceso concluido.
) else (
    echo Operación cancelada.
)
pause
