@echo off
setlocal

set "APP_ROOT=%~dp0"
set "VENV_PYTHON=%APP_ROOT%.venv\Scripts\python.exe"

if not exist "%VENV_PYTHON%" (
    echo [ERROR] No se encontro el Python del entorno virtual:
    echo         "%VENV_PYTHON%"
    pause
    exit /b 1
)

pushd "%APP_ROOT%" >nul

echo =========================================
echo  Construyendo ejecutable de Audio2Text
echo =========================================

echo.
echo Limpiando builds anteriores...
if exist build rmdir /s /q build
if exist dist\Audio2Text rmdir /s /q dist\Audio2Text

echo.
echo Ejecutando PyInstaller...
"%VENV_PYTHON%" -m PyInstaller --clean audio2text.spec

echo.
if exist dist\Audio2Text\Audio2Text.exe (
    echo [EXITO] Ejecutable creado en dist\Audio2Text\Audio2Text.exe
) else (
    echo [ERROR] Fallo al crear el ejecutable.
)
echo.
popd >nul
pause
