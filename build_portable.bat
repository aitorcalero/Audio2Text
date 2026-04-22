@echo off
setlocal

set "APP_ROOT=%~dp0"
if "%APP_ROOT:~-1%"=="\" set "APP_ROOT=%APP_ROOT:~0,-1%"

set "VENV_PYTHON=%APP_ROOT%\.venv\Scripts\python.exe"
if not exist "%VENV_PYTHON%" (
    echo [ERROR] No se encontro el Python del entorno virtual:
    echo         "%VENV_PYTHON%"
    if not defined AUDIO2TEXT_NO_PAUSE pause
    exit /b 1
)

for /f "usebackq tokens=1,* delims==" %%A in ("%APP_ROOT%\.venv\pyvenv.cfg") do (
    if /I "%%A"=="home " (
        for /f "tokens=* delims= " %%I in ("%%B") do set "BASE_PYTHON=%%I"
    )
)

if not defined BASE_PYTHON (
    echo [ERROR] No se pudo resolver sys.base_prefix desde el entorno virtual.
    if not defined AUDIO2TEXT_NO_PAUSE pause
    exit /b 1
)

if not exist "%BASE_PYTHON%\pythonw.exe" (
    echo [ERROR] No se encontro pythonw.exe en la instalacion base:
    echo         "%BASE_PYTHON%"
    if not defined AUDIO2TEXT_NO_PAUSE pause
    exit /b 1
)

set "OUT_DIR=%APP_ROOT%\dist\Audio2TextPortable"
set "RUNTIME_DIR=%OUT_DIR%\runtime"
set "MODEL_CACHE=%LOCALAPPDATA%\Audio2Text\models"

echo =========================================
echo  Construyendo carpeta portable Audio2Text
echo =========================================
echo.
echo Python base: %BASE_PYTHON%
echo Salida:      %OUT_DIR%

if exist "%OUT_DIR%" (
    echo.
    echo Limpiando salida anterior...
    rmdir /s /q "%OUT_DIR%"
)

mkdir "%OUT_DIR%" || goto :build_error
mkdir "%RUNTIME_DIR%" || goto :build_error

echo.
echo Copiando runtime base de Python...
robocopy "%BASE_PYTHON%" "%RUNTIME_DIR%" /E /R:1 /W:1 /NFL /NDL /NJH /NJS /NP /XD "__pycache__" "Doc" "docs" "Tools" "Scripts" "share"
if errorlevel 8 goto :build_error

echo.
echo Copiando dependencias del entorno virtual...
robocopy "%APP_ROOT%\.venv\Lib\site-packages" "%RUNTIME_DIR%\Lib\site-packages" /E /R:1 /W:1 /NFL /NDL /NJH /NJS /NP /XD "__pycache__"
if errorlevel 8 goto :build_error

echo.
echo Copiando archivos de la aplicacion...
copy /Y "%APP_ROOT%\main.py" "%OUT_DIR%\" >nul || goto :build_error
copy /Y "%APP_ROOT%\audio_processor.py" "%OUT_DIR%\" >nul || goto :build_error
copy /Y "%APP_ROOT%\config_manager.py" "%OUT_DIR%\" >nul || goto :build_error
copy /Y "%APP_ROOT%\gui_components.py" "%OUT_DIR%\" >nul || goto :build_error
copy /Y "%APP_ROOT%\output_manager.py" "%OUT_DIR%\" >nul || goto :build_error
copy /Y "%APP_ROOT%\text_processing.py" "%OUT_DIR%\" >nul || goto :build_error
copy /Y "%APP_ROOT%\transcription_services.py" "%OUT_DIR%\" >nul || goto :build_error
copy /Y "%APP_ROOT%\simple_dialog.py" "%OUT_DIR%\" >nul || goto :build_error
copy /Y "%APP_ROOT%\config.example.json" "%OUT_DIR%\config.json" >nul || goto :build_error
copy /Y "%APP_ROOT%\portable_runtime_gui.bat" "%OUT_DIR%\Audio2Text.bat" >nul || goto :build_error
copy /Y "%APP_ROOT%\portable_runtime_console.bat" "%OUT_DIR%\Audio2Text_Console.bat" >nul || goto :build_error

if exist "%APP_ROOT%\ffmpeg.exe" (
    echo.
    echo Copiando ffmpeg.exe...
    copy /Y "%APP_ROOT%\ffmpeg.exe" "%OUT_DIR%\" >nul || goto :build_error
)

if exist "%MODEL_CACHE%" (
    echo.
    echo Copiando modelo local cacheado...
    robocopy "%MODEL_CACHE%" "%OUT_DIR%\models" /E /R:1 /W:1 /NFL /NDL /NJH /NJS /NP
    if errorlevel 8 goto :build_error
)

echo.
echo [EXITO] Carpeta portable creada en:
echo         %OUT_DIR%
echo.
echo Lanzadores:
echo   - %OUT_DIR%\Audio2Text.bat
echo   - %OUT_DIR%\Audio2Text_Console.bat
echo.
if not defined AUDIO2TEXT_NO_PAUSE pause
exit /b 0

:build_error
echo.
echo [ERROR] No se pudo construir la carpeta portable.
if not defined AUDIO2TEXT_NO_PAUSE pause
exit /b 1
