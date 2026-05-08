@echo off
:: Convierte el Resumen del dia a HTML y lo publica en GitHub Pages.
:: Se ejecuta automaticamente por la tarea programada "PublicarResumenDF".

cd /d "%~dp0"
python publicar.py --wait 20 >> publicar.log 2>&1
exit /b %errorlevel%
