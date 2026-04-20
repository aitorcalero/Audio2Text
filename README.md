# Audio2Text

Aplicacion de escritorio y linea de comandos para transcribir audio con OpenAI Whisper o ElevenLabs, con generacion opcional de resumenes y empaquetado para Windows.

## Estado Actual

- `main.py` es el punto de entrada principal.
- `audio2text_refactored.py` se conserva solo como wrapper de compatibilidad.
- La aplicacion puede pedir las API keys en el primer arranque si no encuentra configuracion.
- La configuracion y los logs se guardan en una ruta segura para el ejecutable Windows.

## Funcionalidades

- Seleccion de servicio de transcripcion: OpenAI Whisper o ElevenLabs.
- Interfaz grafica para elegir el audio y el archivo de salida.
- Modo CLI para automatizar ejecuciones.
- Normalizacion de audio y division automatica de archivos grandes.
- Resumenes opcionales con OpenAI.
- Salidas limitadas a formatos de texto seguros (`.txt` y `.md`).
- Empaquetado con PyInstaller.

## Requisitos

- Python 3.10 o superior recomendado.
- `ffmpeg` en `PATH` o `ffmpeg.exe` junto al proyecto o al ejecutable.
- API key de OpenAI para Whisper y para los resumenes.
- API key de ElevenLabs si quieres usar ese servicio.

## Instalacion

```bash
git clone https://github.com/aitorcalero/Audio2Text.git
cd Audio2Text
python -m venv .venv
```

```bash
# Windows
.venv\Scripts\activate
pip install -r requirements.txt
```

## Configuracion

Tienes dos formas de configurar la aplicacion:

1. Primer arranque guiado.
   Si no hay claves configuradas, la interfaz muestra un dialogo para introducirlas y las guarda automaticamente.

2. Archivo manual.

```bash
copy config.example.json config.json
```

Despues edita `config.json` con tus claves reales.

### Orden de carga de configuracion

El proyecto busca `config.json` en este orden:

1. Ruta indicada en la variable de entorno `AUDIO2TEXT_CONFIG`.
2. Directorio actual o junto al ejecutable.
3. Directorio del bundle de PyInstaller.
4. `%LOCALAPPDATA%\Audio2Text\config.json`.

En Windows, cuando la aplicacion guarda configuracion nueva, lo hace en `%LOCALAPPDATA%\Audio2Text\config.json`.

### Parametros principales

- `TRANSCRIPTION_SERVICE`: `openai` o `elevenlabs`.
- `FILE_SIZE_LIMIT_MB`: umbral para dividir audios grandes.
- `CHUNK_DURATION_MIN`: duracion de cada segmento.
- `WHISPER_MODEL`: modelo de Whisper para OpenAI.
- `OPENAI_ENGINE`: modelo usado para generar resumenes.
- `IDIOMA_FORZADO`: vacio para deteccion automatica o codigo como `es`/`en`.

## Uso

### Modo grafico

```bash
python main.py
```

### Modo linea de comandos

```bash
python main.py input.mp3 output.txt
python main.py input.wav output.txt es
```

El tercer argumento es opcional y permite forzar el idioma.
La salida debe guardarse como `.txt` o `.md`.

## Logs

En Windows, el log de la aplicacion se escribe en:

```text
%LOCALAPPDATA%\Audio2Text\logs\audio2text.log
```

## Pruebas Unitarias

La suite versionada cubre la carga segura de configuracion para evitar lecturas indebidas de archivos no JSON o demasiado grandes.

```bash
python -m unittest discover -s unit_tests -p "unit_*.py"
```

## Build Windows

```bash
build_exe.bat
```

Salida esperada:

```text
dist\Audio2Text\Audio2Text.exe
```

Por seguridad, `ffmpeg.exe` no se empaqueta automaticamente aunque exista en la raiz del proyecto.
Si quieres incluirlo de forma explicita:

```bash
set AUDIO2TEXT_BUNDLE_FFMPEG=1
set AUDIO2TEXT_FFMPEG_PATH=C:\ruta\verificada\ffmpeg.exe
build_exe.bat
```

## Estructura Principal

```text
Audio2Text/
|- main.py
|- audio2text_refactored.py
|- gui_components.py
|- simple_dialog.py
|- config_manager.py
|- audio_processor.py
|- transcription_services.py
|- text_processing.py
|- output_manager.py
|- config.example.json
|- requirements.txt
|- audio2text.spec
`- build_exe.bat
```

## GitHub

Las notas rapidas para preparar y subir el repo siguen en `GITHUB_SETUP.md` y `CONECTAR_GITHUB.md`.
