# Audio2Text - Aplicación de Transcripción de Audio

Una aplicación robusta y modular para convertir archivos de audio a texto usando IA, con soporte para **OpenAI Whisper** y **ElevenLabs**.

## 🚀 Características

- **Arquitectura modular**: Código separado en módulos especializados
- **Soporte para ElevenLabs**: Alternativa a OpenAI Whisper para transcripción
- **Interfaz mejorada**: GUI intuitiva con diálogos de progreso
- **Manejo de errores mejorado**: Recuperación automática y logging detallado
- **Configuración flexible**: Fácil cambio entre servicios de transcripción
- **Procesamiento por lotes**: Soporte para archivos grandes con división automática

## 📋 Requisitos

- Python 3.7 o superior
- Clave API de OpenAI (para Whisper y GPT)
- Clave API de ElevenLabs (opcional, para usar su servicio de transcripción)

## 🔧 Instalación y Configuración

### 1. Clonar el repositorio
```bash
git clone <repository-url>
cd Audio2Text
```

### 2. Crear entorno virtual
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate
```

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 4. Configurar API Keys

1. Copia el archivo de configuración de ejemplo:
```bash
copy config.example.json config.json
```

2. Edita `config.json` y añade tus API keys:
```json
{
    "OPENAI_API_KEY": "sk-tu_api_key_de_openai_aqui",
    "ELEVENLABS_API_KEY": "sk_tu_api_key_de_elevenlabs_aqui",
    "TRANSCRIPTION_SERVICE": "openai"
}
```

**⚠️ IMPORTANTE**: Nunca subas el archivo `config.json` a GitHub. Las API keys son privadas.

## 🚀 Uso

### Interfaz Gráfica (Recomendado)
```bash
python audio2text_refactored.py
```

### Línea de Comandos
```bash
python audio2text_refactored.py archivo_audio.mp3 salida.txt
```

## 📁 Estructura del Proyecto

```
Audio2Text/
├── audio2text_refactored.py    # Aplicación principal
├── config_manager.py           # Gestión de configuración
├── audio_processor.py          # Procesamiento de audio
├── transcription_services.py   # Servicios de transcripción (OpenAI/ElevenLabs)
├── text_processing.py          # Procesamiento de texto y resúmenes
├── output_manager.py           # Gestión de archivos de salida
├── gui_components_fixed.py     # Interfaz gráfica
├── simple_dialog.py           # Diálogos simplificados
├── config.example.json        # Plantilla de configuración
├── requirements.txt           # Dependencias de Python
├── .gitignore                # Archivos a ignorar en Git
└── old/                      # Archivos obsoletos
```

## 🔑 Obtener API Keys

### OpenAI
1. Ve a [OpenAI API](https://platform.openai.com/api-keys)
2. Crea una cuenta o inicia sesión
3. Genera una nueva API key
4. Cópiala en el campo `OPENAI_API_KEY` del config.json

### ElevenLabs
1. Ve a [ElevenLabs](https://elevenlabs.io/)
2. Crea una cuenta o inicia sesión
3. Ve a tu perfil y obtén tu API key
4. Cópiala en el campo `ELEVENLABS_API_KEY` del config.json

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
    "OPENAI_API_KEY": "tu_clave_aqui",
    "WHISPER_MODEL": "whisper-1"
}
```

#### ElevenLabs
```json
{
    "TRANSCRIPTION_SERVICE": "elevenlabs",
    "ELEVENLABS_API_KEY": "tu_clave_aqui"
}
```

### Parámetros Principales

| Parámetro | Descripción | Valor por defecto |
|-----------|-------------|------------------|
| `TRANSCRIPTION_SERVICE` | Servicio a usar (`openai` o `elevenlabs`) | `openai` |
| `FILE_SIZE_LIMIT_MB` | Límite de tamaño antes de dividir archivos | `24` |
| `CHUNK_DURATION_MIN` | Duración de chunks en minutos | `10` |
| `IDIOMA_FORZADO` | Fuerza un idioma específico | `es` |
| `TEXT_WRAP_LIMIT` | Límite de caracteres por chunk de texto | `3000` |
| `MAX_SUMMARY_TOKENS` | Tokens máximos para resúmenes | `300` |

## 📁 Estructura del Proyecto

```
Audio2Text/
├── audio2text_refactored.py      # Aplicación principal
├── config_manager.py             # Gestión de configuración
├── audio_processor.py            # Procesamiento de audio
├── transcription_services.py     # Servicios de transcripción (OpenAI/ElevenLabs)
├── text_processing.py            # Análisis de texto y resúmenes
├── output_manager.py             # Gestión de archivos de salida
├── gui_components_fixed.py       # Componentes de interfaz gráfica
├── config_new.json               # Plantilla de configuración
├── requirements.txt              # Dependencias
└── README.md                     # Este archivo
```

## 🔄 Comparación con la Versión Original

### Mejoras Arquitectónicas

| Aspecto | Original | Refactorizado |
|---------|----------|---------------|
| **Estructura** | Monolítico (1 archivo) | Modular (7 módulos) |
| **Servicios** | Solo OpenAI | OpenAI + ElevenLabs |
| **Configuración** | Hardcodeada | Clase ConfigManager |
| **Manejo de errores** | Básico | Robusto con recovery |
| **Testing** | Difícil | Fácil (módulos independientes) |
| **Extensibilidad** | Limitada | Alta (patrón Strategy) |

### Nuevas Características

1. **Soporte ElevenLabs**: Alternativa moderna para transcripción
2. **Progreso visual**: Barras de progreso detalladas
3. **Configuración GUI**: Interfaz para cambiar configuración
4. **Backup automático**: Respaldo de archivos existentes
5. **Logging mejorado**: Logs estructurados y detallados
6. **Validación robusta**: Verificación de archivos y configuración

## 🔌 Cómo Usar ElevenLabs

1. **Obtener clave API:**
   - Registrarse en [ElevenLabs](https://elevenlabs.io/)
   - Ir a Profile → API Keys
   - Copiar tu clave API

2. **Configurar:**
   ```json
   {
       "TRANSCRIPTION_SERVICE": "elevenlabs",
       "ELEVENLABS_API_KEY": "tu_clave_elevenlabs"
   }
   ```

3. **Ejecutar:**
   - La aplicación usará automáticamente ElevenLabs para transcripción
   - OpenAI seguirá siendo usado para los resúmenes

## 🐛 Solución de Problemas

### Error de clave API
```
Error en la configuración: ELEVENLABS_API_KEY no está configurado
```
**Solución:** Añadir la clave API correcta en `config.json`

### Error de archivo grande
```
Error dividiendo el audio
```
**Solución:** Verificar que FFmpeg esté instalado para pydub

### Error de conexión
```
Error de conexión con ElevenLabs
```
**Solución:** Verificar conexión a internet y validez de la clave API

## 📝 Logs

Los logs se guardan automáticamente en `audio_to_text.log` con información detallada sobre:
- Inicialización de componentes
- Progreso de transcripción
- Análisis de texto
- Errores y advertencias

## 🔮 Futuras Mejoras

- [ ] Soporte para más servicios de IA (Google Cloud, Azure)
- [ ] Interfaz web con Flask/FastAPI
- [ ] Procesamiento en tiempo real
- [ ] Soporte para video (extracción de audio)
- [ ] Traducción automática
- [ ] API REST para integración

## 📄 Licencia

Este proyecto es una refactorización de la aplicación Audio2Text original, mejorada para ser más robusta, modular y extensible.