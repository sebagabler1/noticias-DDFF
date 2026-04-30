@echo off
:: Verifica conexion a internet antes de scrapear
ping -n 1 -w 3000 8.8.8.8 >nul 2>&1
if errorlevel 1 (
    exit /b 0
)
:: Hay internet, ejecutar scraper en silencio
cd /d "%~dp0"
python "%~dp0scraper_df.py" --modo dia
