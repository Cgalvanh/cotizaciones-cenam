@echo off
title Sistema CENAM - Nube Segura (Local Test)
echo ========================================================
echo  Iniciando Plataforma Nube Segura (Zero Trust / RBAC)
echo ========================================================
echo.
cd nube_segura
python -m streamlit run app_cloud.py
pause
