# Audio2Text - Transcripción de Audio con IA

Aplicación para convertir archivos de audio a texto usando **OpenAI Whisper** y **ElevenLabs**, con interfaz gráfica intuitiva y procesamiento por lotes.

## ✨ Características Principales

- **Doble soporte de IA**: OpenAI Whisper y ElevenLabs para máxima flexibilidad
- **Interfaz gráfica**: Selección fácil de servicios y archivos
- **Procesamiento inteligente**: División automática de archivos grandes
- **Detección de idioma**: Automática o manual
- **Resúmenes automáticos**: Generación de resúmenes con GPT
- **Múltiples formatos**: MP3, WAV, M4A, MP4 y más

## 📋 Requisitos

- Python 3.7 o superior
- API Key de OpenAI (para Whisper y resúmenes con GPT)
- API Key de ElevenLabs (opcional, para transcripción alternativa)

## � Instalación Rápida

### 1. Clonar y configurar
```bash
git clone https://github.com/aitorcalero/Audio2Text.git
cd Audio2Text
python -m venv .venv
```

### 2. Activar entorno e instalar
```bash
# Windows
.venv\Scripts\activate
# Linux/Mac  
source .venv/bin/activate

pip install -r requirements.txt
```

### 3. Configurar API Keys
```bash
# Copiar plantilla de configuración
copy config.example.json config.json

# Editar config.json con tus API keys
```

Ejemplo de `config.json`:
```json
{
{
    "OPENAI_API_KEY": "sk-tu_api_key_de_openai_aqui",
    "ELEVENLABS_API_KEY": "sk_tu_api_key_de_elevenlabs_aqui", 
    "TRANSCRIPTION_SERVICE": "openai"
}
```

**⚠️ IMPORTANTE**: El archivo `config.json` no se sube a GitHub automáticamente para proteger tus API keys.

## � Uso de la Aplicación

### Modo Gráfico (Recomendado)
```bash
python audio2text_refactored.py
```
1. Selecciona el servicio de transcripción (OpenAI o ElevenLabs)
2. Elige tu archivo de audio
3. Selecciona dónde guardar la transcripción
4. ¡La aplicación procesa automáticamente!

### Modo Línea de Comandos
```bash
python audio2text_refactored.py archivo_audio.mp3 salida.txt
```

## 🎯 Formatos Soportados

**Audio**: MP3, WAV, M4A, MP4, AAC, FLAC, OGG
**Salida**: TXT con transcripción y resumen automático

## � Configurar API Keys

### OpenAI Whisper
1. Visita [OpenAI API](https://platform.openai.com/api-keys)
2. Crea una cuenta y genera tu API key
3. Agrega créditos para usar Whisper (~$0.006 por minuto)

### ElevenLabs (Alternativa)
1. Visita [ElevenLabs](https://elevenlabs.io/)
2. Regístrate y obtén tu API key
3. Servicio alternativo con diferentes capacidades

## 📁 Estructura de Archivos

```
Audio2Text/
├── audio2text_refactored.py    # 🚀 Aplicación principal
├── config_manager.py           # ⚙️ Configuración
├── transcription_services.py   # 🎙️ OpenAI + ElevenLabs  
├── audio_processor.py          # 🎵 Procesamiento de audio
├── text_processing.py          # 📝 Resúmenes con GPT
├── gui_components_fixed.py     # 🖥️ Interfaz gráfica
├── output_manager.py           # 💾 Gestión de archivos
├── config.example.json         # 📋 Plantilla de configuración
└── requirements.txt            # 📦 Dependencias Python
```

## 🔧 Instalación

1. **Clonar o descargar el código**
2. **Instalar dependencias:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configurar las claves API:**
   - Copia `config_new.json` a `config.json`
   - Edita `config.json` y añade tus claves API:
   ```json
   {
       "OPENAI_API_KEY": "tu_clave_openai_aqui",
       "ELEVENLABS_API_KEY": "tu_clave_elevenlabs_aqui",
       "TRANSCRIPTION_SERVICE": "openai"
   }
   ```

## 🎯 Uso

### Modo Interfaz Gráfica (Recomendado)
```bash
python audio2text_refactored.py
```

### Modo Línea de Comandos
```bash
python audio2text_refactored.py input.mp3 output.txt [idioma]
```

Ejemplos:
- `python audio2text_refactored.py audio.mp3 transcript.txt`
- `python audio2text_refactored.py audio.wav transcript.txt es`

## ⚙️ Configuración

### Servicios de Transcripción

#### OpenAI Whisper (Por defecto)
```json
{
    "TRANSCRIPTION_SERVICE": "openai",
## ⚙️ Configuración Avanzada

### Parámetros Principales

| Parámetro | Descripción | Valor por defecto |
|-----------|-------------|------------------|
| `TRANSCRIPTION_SERVICE` | Servicio a usar (`openai` o `elevenlabs`) | `openai` |
| `FILE_SIZE_LIMIT_MB` | Límite antes de dividir archivos | `24` |
| `CHUNK_DURATION_MIN` | Duración de chunks en minutos | `10` |
| `IDIOMA_FORZADO` | Idioma específico (`es`, `en`, etc.) | `es` |
| `WHISPER_MODEL` | Modelo de Whisper a usar | `whisper-1` |

## 🎯 Casos de Uso

- **📚 Transcripción de conferencias y reuniones**
- **🎙️ Conversión de podcasts a texto**
- **📖 Subtitulado de videos educativos**
- **📝 Generación de resúmenes automáticos**
- **🔍 Análisis de contenido de audio**

## 🛠️ Desarrollo y Contribución

### Estructura Modular
```
📁 Módulos principales:
├── 🎵 audio_processor.py      # Procesamiento de archivos de audio
├── 🤖 transcription_services  # APIs de OpenAI y ElevenLabs  
├── 📝 text_processing.py      # Análisis y resúmenes con GPT
├── 🖥️ gui_components_fixed.py # Interfaz gráfica
├── ⚙️ config_manager.py       # Gestión de configuración
└── 💾 output_manager.py       # Archivos de salida

📁 Archivos de prueba: /tests
```

### Para Contribuir
1. Fork del repositorio
2. Crear rama feature: `git checkout -b nueva-funcionalidad`
3. Commit cambios: `git commit -m 'Agregar nueva funcionalidad'`
4. Push a la rama: `git push origin nueva-funcionalidad`
5. Crear Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para más detalles.

## 🤝 Soporte

- **Issues**: [GitHub Issues](https://github.com/aitorcalero/Audio2Text/issues)
- **Documentación**: Ver archivos `GITHUB_SETUP.md` y `CONECTAR_GITHUB.md`
---

**Desarrollado con ❤️ para facilitar la transcripción de audio usando IA**

## 📄 Licencia

Este proyecto es una refactorización de la aplicación Audio2Text original, mejorada para ser más robusta, modular y extensible.