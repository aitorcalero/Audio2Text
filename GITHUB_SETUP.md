# Guia para Subir el Proyecto a GitHub

## Que Debe Subirse

Archivos principales del proyecto:

- `main.py`
- `audio2text_refactored.py`
- `gui_components.py`
- `simple_dialog.py`
- `config_manager.py`
- `audio_processor.py`
- `transcription_services.py`
- `text_processing.py`
- `output_manager.py`
- `config.example.json`
- `requirements.txt`
- `audio2text.spec`
- `build_exe.bat`
- `README.md`
- `.gitignore`

## Que No Debe Subirse

- `config.json`
- `config-*.json`
- `.venv/`, `build/`, `dist/`, `__pycache__/`
- audios, transcripciones, logs y binarios locales como `ffmpeg.exe`

## Flujo Recomendado

```bash
git status
git add .
git commit -m "Limpiar proyecto y consolidar version actual"
git push -u origin main
```

## Verificaciones Utiles

```bash
git check-ignore config.json
git check-ignore ffmpeg.exe
git ls-files --others --ignored --exclude-standard
```

Si `git status` muestra `config.json` o archivos `*-ESRI-*`, revisa `.gitignore` antes de hacer el push.
