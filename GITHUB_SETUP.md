# Guía para Subir el Proyecto a GitHub

## 🔒 Seguridad

Este proyecto incluye un archivo `.gitignore` que protege automáticamente:
- ✅ API keys en `config.json`
- ✅ Archivos de audio personales
- ✅ Logs y archivos temporales
- ✅ Entornos virtuales
- ✅ Cachés de Python

## 📋 Pasos para Subir a GitHub

### 1. Inicializar Git (solo la primera vez)
```bash
git init
```

### 2. Añadir archivos seguros
```bash
git add .
```

### 3. Verificar qué se va a subir
```bash
git status
```

**✅ Debería mostrar:**
- `audio2text_refactored.py`
- `config_manager.py`
- `audio_processor.py`
- `transcription_services.py`
- `text_processing.py`
- `output_manager.py`
- `gui_components_fixed.py`
- `simple_dialog.py`
- `config.example.json` ⬅️ SIN API keys
- `requirements.txt`
- `README.md`
- `.gitignore`

**❌ NO debería mostrar:**
- `config.json` ⬅️ Con API keys reales
- Archivos `.mp3`, `.wav`, etc.
- Carpeta `.venv/`
- Archivos en `old/`

### 4. Hacer commit
```bash
git commit -m "Aplicación Audio2Text refactorizada - versión modular"
```

### 5. Conectar con GitHub
```bash
git remote add origin https://github.com/tu-usuario/Audio2Text.git
```

### 6. Subir código
```bash
git push -u origin main
```

## 🔧 Configuración para Otros Usuarios

Cuando alguien clone tu repositorio:

1. **Clonar**:
```bash
git clone https://github.com/tu-usuario/Audio2Text.git
cd Audio2Text
```

2. **Configurar entorno**:
```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

3. **Configurar API keys**:
```bash
copy config.example.json config.json
# Editar config.json con sus propias API keys
```

## ⚠️ Recordatorios Importantes

- ✅ **NUNCA** hagas `git add config.json` directamente
- ✅ **SIEMPRE** usa `config.example.json` como plantilla
- ✅ **REVISA** `git status` antes de hacer commit
- ✅ **MANTÉN** actualizado el `.gitignore`

## 🚀 Comandos Útiles

```bash
# Ver estado
git status

# Ver qué archivos están siendo ignorados
git ls-files --others --ignored --exclude-standard

# Verificar que config.json NO aparece
git check-ignore config.json  # Debería decir "config.json"

# Añadir cambios
git add .
git commit -m "Descripción de cambios"
git push
```