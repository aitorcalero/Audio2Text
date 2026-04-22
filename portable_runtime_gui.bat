@echo off
setlocal

set "APP_ROOT=%~dp0"
if "%APP_ROOT:~-1%"=="\" set "APP_ROOT=%APP_ROOT:~0,-1%"

set "RUNTIME=%APP_ROOT%\runtime"
set "PYTHONW=%RUNTIME%\pythonw.exe"
set "MAIN_SCRIPT=%APP_ROOT%\main.py"

if not exist "%PYTHONW%" (
    echo [ERROR] No se encontro pythonw.exe en "%PYTHONW%"
    pause
    exit /b 1
)

if not exist "%MAIN_SCRIPT%" (
    echo [ERROR] No se encontro main.py en "%MAIN_SCRIPT%"
    pause
    exit /b 1
)

set "PYTHONHOME=%RUNTIME%"
set "PATH=%RUNTIME%;%RUNTIME%\DLLs;%APP_ROOT%;%PATH%"
set "AUDIO2TEXT_CONFIG=%APP_ROOT%\config.json"
set "HF_HUB_DISABLE_SYMLINKS_WARNING=1"

if exist "%APP_ROOT%\models" set "AUDIO2TEXT_MODELS_DIR=%APP_ROOT%\models"
if exist "%APP_ROOT%\ffmpeg.exe" set "FFMPEG_BINARY=%APP_ROOT%\ffmpeg.exe"
if exist "%RUNTIME%\tcl\tcl8.6" set "TCL_LIBRARY=%RUNTIME%\tcl\tcl8.6"
if exist "%RUNTIME%\tcl\tk8.6" set "TK_LIBRARY=%RUNTIME%\tcl\tk8.6"

pushd "%APP_ROOT%" >nul
"%PYTHONW%" "%MAIN_SCRIPT%" %*
set "EXIT_CODE=%ERRORLEVEL%"
popd >nul

if not "%EXIT_CODE%"=="0" (
    echo.
    echo [ERROR] Audio2Text finalizo con codigo %EXIT_CODE%.
    pause
)

exit /b %EXIT_CODE%
