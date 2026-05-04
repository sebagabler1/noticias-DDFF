@echo off
:: Instala la tarea programada para ejecutar el scraper a las 11:15 todos los dias
set SCRIPT=%~dp0ejecutar_hoy_automatico.bat

schtasks /create ^
  /tn "ScraperDiarioFinanciero" ^
  /tr "\"%SCRIPT%\"" ^
  /sc daily ^
  /st 11:15 ^
  /ru "%USERNAME%" ^
  /f

if errorlevel 1 (
    echo.
    echo ERROR: No se pudo crear la tarea. Intenta ejecutar como Administrador.
    timeout /t 5 >nul
    exit /b 1
)

echo.
echo Tarea programada creada correctamente.
echo Todos los dias a las 11:15 se ejecutara el scraper automaticamente.
echo Si no hay internet, no hace nada.
echo.
echo Para verificarla: Buscador de Windows -^> "Programador de tareas" -^> ScraperDiarioFinanciero
