# Audio2Text

Aplicacion de escritorio y linea de comandos para transcribir audio con OpenAI Whisper o ElevenLabs, con generacion opcional de resumenes y empaquetado para Windows.

## Que Incluye

- Interfaz grafica para elegir servicio, archivo de entrada y destino de salida.
- Modo CLI para automatizar transcripciones.
- Division automatica de audios grandes y normalizacion previa.
- Configuracion segura fuera del directorio del bundle en ejecutables Windows.
- Script y spec de PyInstaller para generar `dist\Audio2Text\Audio2Text.exe`.

## Requisitos

- Python 3.10 o superior recomendado.
- `ffmpeg` disponible en `PATH` o `ffmpeg.exe` junto al ejecutable/proyecto.
- API key de OpenAI para Whisper y resumenes.
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
copy config.example.json config.json
```

Edita `config.json` con tus claves reales. El repositorio ignora `config.json` para no subir secretos.

## Uso

Modo grafico:

```bash
python main.py
```

Modo linea de comandos:

```bash
python main.py input.mp3 output.txt
python main.py input.wav output.txt es
```

`audio2text_refactored.py` se conserva como wrapper de compatibilidad y delega en `main.py`.

## Configuracion

`config.example.json` incluye los parametros principales:

- `TRANSCRIPTION_SERVICE`: `openai` o `elevenlabs`
- `FILE_SIZE_LIMIT_MB`: umbral para partir audios
- `CHUNK_DURATION_MIN`: duracion de cada segmento
- `WHISPER_MODEL`: modelo de transcripcion de OpenAI
- `OPENAI_ENGINE`: modelo usado para resumenes
- `IDIOMA_FORZADO`: vacio para deteccion automatica

## Estructura

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

## Build Windows

```bash
build_exe.bat
```

Resultado esperado:

```text
dist\Audio2Text\Audio2Text.exe
```

## GitHub

Las notas rapidas para preparar y subir el repo estan en `GITHUB_SETUP.md` y `CONECTAR_GITHUB.md`.
