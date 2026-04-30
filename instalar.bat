@echo off
:: ─────────────────────────────────────────────────────────────────────────────
:: instalar.bat  —  Instala dependencias y programa el scraper diario
:: Ejecutar como Administrador la primera vez
:: ─────────────────────────────────────────────────────────────────────────────

echo.
echo ==========================================
echo   INSTALADOR - Scraper DF.cl para Claude
echo ==========================================
echo.

:: Verificar Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python no encontrado. Descargalo de https://python.org
    timeout /t 5 >nul
    exit /b 1
)
echo [OK] Python encontrado

:: Instalar dependencias
echo.
echo Instalando dependencias...
pip install requests beautifulsoup4 python-docx --quiet
if errorlevel 1 (
    echo [ERROR] Fallo la instalacion de dependencias
    timeout /t 5 >nul
    exit /b 1
)
echo [OK] Dependencias instaladas

:: Obtener ruta del script
set SCRIPT_DIR=%~dp0
set SCRIPT_PATH=%SCRIPT_DIR%scraper_df.py

echo.
echo Configurando tarea programada diaria...

:: Crear tarea en el Programador de Windows (lunes a viernes a las 8:00 AM)
schtasks /create /tn "Scraper DF Diario" ^
    /tr "python \"%SCRIPT_PATH%\"" ^
    /sc WEEKLY ^
    /d MON,TUE,WED,THU,FRI ^
    /st 08:00 ^
    /f >nul 2>&1

if errorlevel 1 (
    echo [AVISO] No se pudo crear la tarea automatica.
    echo         Puedes ejecutar el script manualmente con: ejecutar_hoy.bat
) else (
    echo [OK] Tarea programada: lunes a viernes a las 8:00 AM
)

echo.
echo ==========================================
echo   Instalacion completada
echo ==========================================
echo.
echo Archivos Word se guardaran en:
echo   %USERPROFILE%\Desktop\Noticias_DF\
echo.
echo Comandos disponibles:
echo   ejecutar_hoy.bat       -^> Scrapea el dia de hoy
echo   ejecutar_semana.bat    -^> Scrapea los ultimos 7 dias
echo   ejecutar_con_resumenes.bat -^> Incluye resumen de articulos
echo.
