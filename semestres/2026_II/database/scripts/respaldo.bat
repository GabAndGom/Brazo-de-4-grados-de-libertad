@echo off
rem Respaldo diario de la base brazo4gdl en Windows (guía 8, tarea 63). Conserva los últimos 30.
rem Programarlo: Programador de tareas > Crear tarea básica > Diariamente 23:00 > Iniciar programa: este .bat
rem Requiere pg_dump en el PATH (C:\Program Files\PostgreSQL\16\bin) y la contraseña en %APPDATA%\postgresql\pgpass.conf
setlocal
if "%BRAZO_BASE%"=="" set BRAZO_BASE=brazo4gdl
set DESTINO=%~dp0respaldos
if not exist "%DESTINO%" mkdir "%DESTINO%"
for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyy-MM-dd_HHmm"') do set FECHA=%%i
set ARCHIVO=%DESTINO%\%BRAZO_BASE%_%FECHA%.dump
pg_dump -Fc -f "%ARCHIVO%" %BRAZO_BASE% || exit /b 1
pg_restore -l "%ARCHIVO%" > nul || exit /b 1
echo %date% %time% respaldo %ARCHIVO%
powershell -NoProfile -Command "Get-ChildItem '%DESTINO%\%BRAZO_BASE%_*.dump' | Sort-Object LastWriteTime -Descending | Select-Object -Skip 30 | Remove-Item"
