@echo off
echo =========================================
echo  Construyendo ejecutable de Audio2Text
echo =========================================

echo.
echo Limpiando builds anteriores...
if exist build rmdir /s /q build
if exist dist\Audio2Text rmdir /s /q dist\Audio2Text

echo.
echo Ejecutando PyInstaller...
python -m PyInstaller --clean audio2text.spec

echo.
if exist dist\Audio2Text\Audio2Text.exe (
    echo [EXITO] Ejecutable creado en dist\Audio2Text\Audio2Text.exe
) else (
    echo [ERROR] Fallo al crear el ejecutable.
)
echo.
pause
