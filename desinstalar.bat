@echo off
echo.
echo ==========================================
echo   DESINSTALADOR - Scraper DF.cl
echo ==========================================
echo.
echo Esto eliminara:
echo   - La tarea programada diaria
echo   - Los archivos del scraper (esta carpeta)
echo.
echo Los archivos Word en Noticias_DF del escritorio
echo NO seran eliminados.
echo.
set /p confirm="Estas seguro? (S/N): "
if /i "%confirm%" neq "S" (
    echo Cancelado.
    exit /b 0
)

echo.
echo Eliminando tarea programada...
schtasks /delete /tn "Scraper DF Diario" /f >nul 2>&1
echo [OK] Tarea eliminada

echo Eliminando archivos del scraper...
set SCRIPT_DIR=%~dp0
cd /d %USERPROFILE%
rmdir /s /q "%SCRIPT_DIR%" >nul 2>&1
echo [OK] Archivos eliminados

echo.
echo ==========================================
echo   Desinstalacion completada
echo ==========================================
echo.
echo Los archivos Word en tu escritorio se mantienen.
echo Puedes borrarlos manualmente si quieres.
echo.
