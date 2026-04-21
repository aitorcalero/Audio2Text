@echo off
setlocal

set "APP_ROOT=%~dp0"
set "VENV_PYTHON=%APP_ROOT%.venv\Scripts\python.exe"
set "MAIN_SCRIPT=%APP_ROOT%main.py"

if not exist "%VENV_PYTHON%" (
    echo [ERROR] No se encontro el Python del entorno virtual:
    echo         "%VENV_PYTHON%"
    echo.
    echo Crea o restaura la carpeta .venv antes de lanzar Audio2Text.
    pause
    exit /b 1
)

if not exist "%MAIN_SCRIPT%" (
    echo [ERROR] No se encontro el archivo principal:
    echo         "%MAIN_SCRIPT%"
    pause
    exit /b 1
)

pushd "%APP_ROOT%" >nul
"%VENV_PYTHON%" "%MAIN_SCRIPT%" %*
set "EXIT_CODE=%ERRORLEVEL%"
popd >nul

if not "%EXIT_CODE%"=="0" (
    echo.
    echo [ERROR] Audio2Text finalizo con codigo %EXIT_CODE%.
    pause
)

exit /b %EXIT_CODE%
