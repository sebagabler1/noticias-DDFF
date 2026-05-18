@echo off
:: Instala la tarea programada "PublicarResumenDF" que corre todos los dias a las 11:40
:: (10 minutos despues de Cowork generar el Resumen).

set SCRIPT=%~dp0publicar.bat

schtasks /create ^
  /tn "PublicarResumenDF" ^
  /tr "\"%SCRIPT%\"" ^
  /sc daily ^
  /st 11:40 ^
  /ru "%USERNAME%" ^
  /f

if errorlevel 1 (
    echo.
    echo ERROR: No se pudo crear la tarea. Intenta ejecutar como Administrador.
    timeout /t 5 >nul
    exit /b 1
)

echo.
echo Tarea programada "PublicarResumenDF" creada correctamente.
echo Todos los dias a las 11:40 se publicara el resumen del dia.
echo Si el PC esta apagado, no se ejecuta ese dia (el ultimo resumen publicado se mantiene).
echo.
echo Para verificar: Programador de tareas -^> PublicarResumenDF
echo Para ver logs: el archivo "publicar.log" en esta carpeta.
echo.
pause
