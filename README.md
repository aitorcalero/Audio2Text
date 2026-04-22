# Audio2Text

Audio2Text es una aplicación para Windows que:

- transcribe archivos de audio,
- puede generar un resumen del contenido,
- permite usar transcripción local con `faster-whisper`,
- y también puede usar OpenAI o ElevenLabs.

Este proyecto tiene interfaz gráfica y también se puede lanzar por línea de comandos.

## Qué hace

Con Audio2Text puedes:

- abrir un audio desde una ventana,
- elegir cómo quieres transcribirlo,
- guardar el resultado en `.txt` o `.md`,
- incluir un resumen opcional,
- y ver en el documento final qué servicio se usó, qué modelo se usó, cuánto tardó la transcripción y si la ejecución fue en `GPU`, `CPU` o servicio online.

## Servicios disponibles

Audio2Text puede trabajar de tres formas:

- `local`: usa `faster-whisper` en tu propio equipo.
- `openai`: usa la API de OpenAI.
- `elevenlabs`: usa la API de ElevenLabs.

### Recomendación rápida

- Si quieres usarlo sin claves API: usa `local`.
- Si quieres máxima simplicidad y ya tienes APIs: usa `openai`.
- Si ya trabajas con ElevenLabs: usa `elevenlabs`.

## Requisitos mínimos

No des por supuesto que tu equipo ya tiene nada instalado. Comprueba esto primero.

### 1. Sistema operativo

- Windows 10 o Windows 11.

### 2. Python

Necesitas Python 3.11 instalado.

Para comprobarlo, abre PowerShell y ejecuta:

```powershell
python --version
```

o:

```powershell
py --version
```

Si no aparece una versión de Python, instala Python 3.11 antes de seguir.

### 3. Git

Git es opcional.

- Si vas a clonar el repositorio: necesitas Git.
- Si has descargado el proyecto como `.zip`: no hace falta Git.

Para comprobar si Git está instalado:

```powershell
git --version
```

### 4. FFmpeg

El proyecto necesita `ffmpeg` para procesar audio.

Tienes dos opciones:

- dejar `ffmpeg.exe` en la raíz del proyecto,
- o tener `ffmpeg` instalado en el sistema.

En este repositorio ya existe un `ffmpeg.exe` en la raíz, así que si trabajas desde esta carpeta no necesitas instalar nada más para ese punto.

## Instalación desde cero

### Opción A. Descargar el proyecto con Git

```powershell
git clone https://github.com/aitorcalero/Audio2Text.git
cd Audio2Text
```

### Opción B. Descargar el proyecto como ZIP

1. Descarga el proyecto.
2. Descomprime el ZIP.
3. Abre PowerShell dentro de la carpeta `Audio2Text`.

### Crear el entorno virtual

Ejecuta esto dentro de la carpeta del proyecto:

```powershell
python -m venv .venv
```

Si `python` no funciona pero `py` sí, usa:

```powershell
py -3.11 -m venv .venv
```

### Activar el entorno virtual

En PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Si te da error de ejecución de scripts, usa esta línea solo para la sesión actual:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
```

Y vuelve a ejecutar:

```powershell
.\.venv\Scripts\Activate.ps1
```

### Instalar dependencias

Con el entorno virtual activado:

```powershell
pip install -r requirements.txt
```

Las dependencias actuales del proyecto incluyen:

- `customtkinter`
- `faster-whisper`
- `openai`
- `requests`
- `pydub`
- `langdetect`
- `backoff`
- `pyinstaller`

## Configuración

La forma más fácil de empezar es usar la configuración de ejemplo.

En PowerShell:

```powershell
Copy-Item config.example.json config.json
```

El archivo actual contiene estos valores por defecto:

```json
{
    "OPENAI_API_KEY": "",
    "ELEVENLABS_API_KEY": "",
    "TRANSCRIPTION_SERVICE": "local",
    "LOCAL_WHISPER_MODEL": "large-v3",
    "FILE_SIZE_LIMIT_MB": 24,
    "CHUNK_DURATION_MIN": 10,
    "TEXT_WRAP_LIMIT": 3000,
    "WHISPER_MODEL": "whisper-1",
    "IDIOMA_FORZADO": "",
    "OPENAI_ENGINE": "gpt-4o-mini",
    "MAX_SUMMARY_TOKENS": 300,
    "SUMMARY_TEMPERATURE": 0.3
}
```

### Configuración mínima para empezar

Si quieres empezar sin APIs:

- deja `TRANSCRIPTION_SERVICE` en `local`,
- no rellenes `OPENAI_API_KEY`,
- no rellenes `ELEVENLABS_API_KEY`.

Si quieres usar OpenAI:

- pon `TRANSCRIPTION_SERVICE` en `openai`,
- rellena `OPENAI_API_KEY`.

Si quieres usar ElevenLabs:

- pon `TRANSCRIPTION_SERVICE` en `elevenlabs`,
- rellena `ELEVENLABS_API_KEY`.

### Dónde busca la configuración

La aplicación busca `config.json` en este orden:

1. Ruta indicada en la variable `AUDIO2TEXT_CONFIG`.
2. Carpeta actual o junto al ejecutable/lanzador.
3. Carpeta interna del bundle si se usa PyInstaller.
4. `%LOCALAPPDATA%\Audio2Text\config.json`.

## Primer arranque

Con el entorno virtual activado, ejecuta:

```powershell
python main.py
```

Si todo va bien:

- se abrirá la interfaz,
- podrás elegir el servicio de transcripción,
- luego elegirás el archivo de audio,
- y por último el archivo de salida.

## Uso normal

### Modo gráfico

```powershell
python main.py
```

### Modo línea de comandos

```powershell
python main.py "C:\ruta\audio.m4a" "C:\ruta\salida.md"
```

Si quieres forzar idioma:

```powershell
python main.py "C:\ruta\audio.m4a" "C:\ruta\salida.md" es
```

Notas:

- El archivo de salida debe ser `.txt` o `.md`.
- El tercer parámetro es opcional.
- Si no fuerzas idioma, el sistema intenta detectarlo.

## Lanzadores incluidos

En la raíz del proyecto tienes:

- `Audio2Text.bat`: lanza la app usando `.\.venv\Scripts\python.exe`.
- `build_exe.bat`: construye el paquete PyInstaller.
- `build_portable.bat`: crea una carpeta portable basada en Python firmado.

## Opción portable recomendada

En algunos equipos corporativos, Windows Defender puede bloquear `.exe` generados con PyInstaller aunque estén bien construidos.

Por eso existe una opción portable más robusta:

```powershell
build_portable.bat
```

Eso genera esta carpeta:

```text
dist\Audio2TextPortable
```

Dentro encontrarás:

- `Audio2Text.bat`
- `Audio2Text_Console.bat`
- `runtime\`
- `ffmpeg.exe`
- `config.json`
- `models\` si ya tenías un modelo local descargado

### Qué hace esta carpeta portable

- usa un `pythonw.exe` firmado,
- incluye dependencias,
- incluye `ffmpeg.exe`,
- puede incluir el modelo local ya descargado,
- y evita parte de los bloqueos que pueden afectar a un `.exe` recién generado por PyInstaller.

## Qué incluye el documento final

El archivo `.txt` o `.md` generado por Audio2Text incluye:

- la fecha,
- el idioma detectado,
- el número de partes procesadas,
- el número de resúmenes generados,
- el servicio y modelo de transcripción usados,
- si se ejecutó en `GPU`, `CPU` o servicio online,
- y el tiempo que tardó la transcripción.

## Empaquetado con PyInstaller

Si aun así quieres generar el ejecutable PyInstaller:

```powershell
build_exe.bat
```

La salida queda en:

```text
dist\Audio2Text
```

Importante:

- `dist\Audio2Text\Audio2Text.exe` no es un archivo aislado.
- Debes mover la carpeta completa `dist\Audio2Text`.
- En algunos equipos ese `.exe` puede ser bloqueado por Defender o por políticas corporativas.

## GPU y transcripción local

La transcripción local funciona en CPU y, si el equipo lo permite, también en GPU.

### CPU

No requiere configuración especial adicional.

### GPU NVIDIA

Para GPU con `faster-whisper` necesitas:

- drivers NVIDIA funcionando,
- runtime compatible de CUDA 12,
- cuDNN 9,
- y que esas DLL estén accesibles para el proceso.

Si no están disponibles, la aplicación hará `fallback` a CPU.

## Qué se guarda y dónde

### Logs

En Windows, los logs se guardan en:

```text
%LOCALAPPDATA%\Audio2Text\logs\audio2text.log
```

### Configuración

Cuando la aplicación guarda configuración nueva, normalmente la escribe en:

```text
%LOCALAPPDATA%\Audio2Text\config.json
```

Si usas la carpeta portable y el lanzador fija `AUDIO2TEXT_CONFIG`, entonces también puedes trabajar con el `config.json` que va junto a la aplicación.

### Modelos locales

Por defecto, los modelos locales se descargan en:

```text
%LOCALAPPDATA%\Audio2Text\models
```

Si existe una carpeta `models` junto a la app portable, la aplicación la usa primero.

## Ejecutar pruebas

```powershell
python -m unittest discover -s unit_tests -p "unit_*.py"
```

## Posibles problemas

### 1. `python` no se reconoce

Solución:

- instala Python 3.11,
- o usa `py -3.11` en lugar de `python`.

### 2. No puedes activar `.venv` en PowerShell

Síntoma:

- error de ejecución de scripts.

Solución:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\.venv\Scripts\Activate.ps1
```

### 3. `pip install -r requirements.txt` falla

Posibles causas:

- no estás dentro del entorno virtual,
- tu conexión está bloqueando descargas,
- o estás usando una versión de Python distinta.

Comprueba:

```powershell
python --version
pip --version
```

### 4. La aplicación no encuentra `ffmpeg`

Síntoma:

- errores al abrir o convertir audio.

Solución:

- asegúrate de que `ffmpeg.exe` está en la raíz del proyecto,
- o colócalo junto al lanzador portable,
- o instala `ffmpeg` en el sistema.

### 5. El modo local no usa la GPU

Síntoma:

- la transcripción funciona, pero en CPU.

Causa habitual:

- faltan DLL de CUDA 12 o cuDNN 9.

Solución:

- instala el runtime correcto,
- verifica que la GPU NVIDIA está disponible,
- y revisa el documento de salida, donde ahora se indica si se usó `GPU` o `CPU`.

### 6. El `.exe` de PyInstaller no arranca

Síntoma:

- Windows muestra “Acceso denegado”,
- o “Windows no tiene acceso al dispositivo, ruta de acceso o archivo especificado”.

Causa habitual:

- Windows Defender o una política corporativa bloquea el `.exe`.

Solución recomendada:

- usa la carpeta portable `dist\Audio2TextPortable`,
- o pide a IT una exclusión / allow-list,
- o firma digitalmente el binario si lo vas a distribuir en un entorno gestionado.

### 7. La primera transcripción local tarda mucho

Esto es normal.

Causa:

- `faster-whisper` descarga el modelo la primera vez.

Después de esa primera descarga, las siguientes ejecuciones son más rápidas.

### 8. El resumen no se genera

Síntoma:

- la transcripción sale bien, pero el resumen no.

Causa habitual:

- falta `OPENAI_API_KEY`.

Solución:

- añade tu clave OpenAI en `config.json`,
- o usa solo la transcripción sin resumen.

### 9. El archivo de salida no se guarda

Comprueba:

- que la salida termine en `.txt` o `.md`,
- que la carpeta de destino exista o sea escribible,
- y que el archivo no esté abierto por otro programa.

## Estructura principal del proyecto

```text
Audio2Text/
|- main.py
|- audio_processor.py
|- config_manager.py
|- gui_components.py
|- output_manager.py
|- simple_dialog.py
|- text_processing.py
|- transcription_services.py
|- requirements.txt
|- config.example.json
|- build_exe.bat
|- build_portable.bat
`- audio2text.spec
```

## Resumen rápido

Si solo quieres instalarlo y probarlo en tu equipo:

1. Instala Python 3.11.
2. Abre PowerShell en la carpeta del proyecto.
3. Ejecuta `python -m venv .venv`.
4. Ejecuta `.\.venv\Scripts\Activate.ps1`.
5. Ejecuta `pip install -r requirements.txt`.
6. Ejecuta `Copy-Item config.example.json config.json`.
7. Ejecuta `python main.py`.

Si lo quieres llevar a otro equipo Windows:

1. Ejecuta `build_portable.bat`.
2. Copia la carpeta `dist\Audio2TextPortable`.
3. En el otro equipo, lanza `Audio2Text.bat`.
