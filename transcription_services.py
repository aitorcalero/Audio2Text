"""Servicios de transcripcion para la aplicacion Audio2Text."""

from __future__ import annotations

import concurrent.futures
import logging
import os
from abc import ABC, abstractmethod
from pathlib import Path
import threading
from typing import Any, Dict, Optional

import backoff
import requests

_WINDOWS_DLL_HANDLES: list[Any] = []
_WINDOWS_DLL_LOCK = threading.Lock()


def _get_models_dir() -> Path:
    """Devuelve el directorio seguro donde se almacenan modelos locales."""
    local_appdata = os.environ.get("LOCALAPPDATA")
    if local_appdata:
        return Path(local_appdata) / "Audio2Text" / "models"
    return Path.home() / ".audio2text" / "models"


def _iter_windows_cuda_dirs() -> list[Path]:
    """Localiza directorios plausibles de CUDA y cuDNN en Windows."""
    if os.name != "nt":
        return []

    candidates: list[Path] = []
    env_candidates = [
        os.environ.get("CUDA_PATH"),
        os.environ.get("CUDA_PATH_V12_5"),
    ]

    for key, value in os.environ.items():
        if key.startswith("CUDA_PATH_V") and value:
            env_candidates.append(value)

    for env_path in env_candidates:
        if not env_path:
            continue
        base_path = Path(env_path)
        candidates.append(base_path)
        candidates.append(base_path / "bin")
        candidates.append(base_path / "bin" / "x64")

    cuda_root = Path(r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA")
    if cuda_root.exists():
        for version_dir in sorted(cuda_root.glob("v12*"), reverse=True):
            candidates.append(version_dir / "bin")
            candidates.append(version_dir / "bin" / "x64")

    cudnn_root = Path(r"C:\Program Files\NVIDIA\CUDNN")
    if cudnn_root.exists():
        for version_dir in sorted(cudnn_root.glob("v9*"), reverse=True):
            candidates.extend(sorted(version_dir.glob(r"bin\12*\x64"), reverse=True))
            candidates.extend(sorted(version_dir.glob(r"bin\x64"), reverse=True))

    unique_candidates: list[Path] = []
    seen: set[str] = set()
    for candidate in candidates:
        normalized = str(candidate).lower()
        if normalized in seen or not candidate.is_dir():
            continue
        seen.add(normalized)
        unique_candidates.append(candidate)

    return unique_candidates


def _register_windows_cuda_runtime() -> None:
    """Registra rutas de CUDA/cuDNN para que el proceso pueda resolver DLLs."""
    if os.name != "nt" or not hasattr(os, "add_dll_directory"):
        return

    candidate_dirs = _iter_windows_cuda_dirs()
    if not candidate_dirs:
        return

    with _WINDOWS_DLL_LOCK:
        if _WINDOWS_DLL_HANDLES:
            return

        current_path_entries = os.environ.get("PATH", "").split(os.pathsep)
        known_entries = {entry.lower() for entry in current_path_entries if entry}

        for dll_dir in candidate_dirs:
            dll_dir_str = str(dll_dir)
            if dll_dir_str.lower() not in known_entries:
                os.environ["PATH"] = f"{dll_dir_str}{os.pathsep}{os.environ.get('PATH', '')}"
                known_entries.add(dll_dir_str.lower())

            try:
                _WINDOWS_DLL_HANDLES.append(os.add_dll_directory(dll_dir_str))
            except OSError:
                continue

        if _WINDOWS_DLL_HANDLES:
            logging.info(
                "Rutas CUDA/cuDNN registradas en el proceso: %s",
                ", ".join(str(path) for path in candidate_dirs),
            )


class TranscriptionService(ABC):
    """Interfaz abstracta para servicios de transcripcion."""

    def __init__(self):
        self._last_run_metadata: Dict[str, Any] = {}

    @abstractmethod
    def transcribe(self, audio_file_path: str, language: str = "es") -> Optional[str]:
        """Transcribe un archivo de audio a texto."""

    def get_last_run_metadata(self) -> Dict[str, Any]:
        """Devuelve metadatos del ultimo uso efectivo del servicio."""
        return dict(self._last_run_metadata)

    def _set_last_run_metadata(self, metadata: Dict[str, Any]) -> None:
        """Actualiza los metadatos del ultimo uso del servicio."""
        self._last_run_metadata = dict(metadata)


class MissingConfigTranscriptionService(TranscriptionService):
    """Servicio placeholder cuando faltan credenciales."""

    def __init__(self, reason: str):
        super().__init__()
        self.reason = reason

    def transcribe(self, audio_file_path: str, language: str = "es") -> Optional[str]:
        raise RuntimeError(self.reason)


class OpenAITranscriptionService(TranscriptionService):
    """Servicio de transcripcion usando OpenAI Whisper."""

    def __init__(self, api_key: str, model: str = "whisper-1"):
        super().__init__()
        self.api_key = api_key
        self.model = model

        from openai import OpenAI
        self.client = OpenAI(api_key=api_key)

    @backoff.on_exception(backoff.expo, Exception, max_tries=3)
    def transcribe(self, audio_file_path: str, language: str = "es") -> Optional[str]:
        """
        Transcribe audio usando OpenAI Whisper
        
        Args:
            audio_file_path: Ruta del archivo de audio
            language: Código de idioma (ej: 'es', 'en')
            
        Returns:
            Texto transcrito o None si hay error
        """
        try:
            logging.info(f"Transcribiendo con OpenAI Whisper: {audio_file_path}")
            
            with open(audio_file_path, "rb") as audio_file:
                transcript = self.client.audio.transcriptions.create(
                    model=self.model,
                    file=audio_file,
                    language=language
                )
                text_result = transcript.text
            
            logging.info(f"Transcripción completada: {len(text_result)} caracteres")
            self._set_last_run_metadata(
                {
                    "service_type": "openai",
                    "service_name": "OpenAI Whisper",
                    "provider": "OpenAI",
                    "mode": "online",
                    "model": self.model,
                    "model_identifier": self.model,
                    "execution_target": "Servicio online",
                    "effective_device": "online",
                }
            )
            return text_result
            
        except Exception as e:
            logging.error(f"Error transcribiendo {audio_file_path} con OpenAI: {e}")
            return None


class ElevenLabsTranscriptionService(TranscriptionService):
    """Servicio de transcripcion usando ElevenLabs."""

    def __init__(self, api_key: str):
        super().__init__()
        self.api_key = api_key
        self.base_url = "https://api.elevenlabs.io/v1"
        self.model = "scribe_v1"

    @backoff.on_exception(
        backoff.expo,
        (requests.exceptions.RequestException, Exception),
        max_tries=3,
    )
    def transcribe(self, audio_file_path: str, language: str = "es") -> Optional[str]:
        """
        Transcribe audio usando ElevenLabs
        
        Args:
            audio_file_path: Ruta del archivo de audio
            language: Código de idioma (ej: 'es', 'en')
            
        Returns:
            Texto transcrito o None si hay error
        """
        try:
            logging.info(f"Transcribiendo con ElevenLabs: {audio_file_path}")
            
            url = f"{self.base_url}/speech-to-text"
            headers = {
                "xi-api-key": self.api_key
            }
            
            # ElevenLabs requiere multipart/form-data con model_id obligatorio
            with open(audio_file_path, "rb") as audio_file:
                files = {
                    "file": (os.path.basename(audio_file_path), audio_file, 'audio/mpeg')
                }
                data = {
                    "model_id": self.model  # Modelo correcto de ElevenLabs
                }
                
                response = requests.post(url, headers=headers, files=files, data=data)
                
                logging.debug("ElevenLabs response status: %s", response.status_code)
                
                response.raise_for_status()
            
            result = response.json()
            transcript_text = result.get("text", "")
            
            logging.info(f"Transcripción completada con ElevenLabs: {len(transcript_text)} caracteres")
            self._set_last_run_metadata(
                {
                    "service_type": "elevenlabs",
                    "service_name": "ElevenLabs Speech-to-Text",
                    "provider": "ElevenLabs",
                    "mode": "online",
                    "model": self.model,
                    "model_identifier": self.model,
                    "execution_target": "Servicio online",
                    "effective_device": "online",
                }
            )
            return transcript_text
            
        except requests.exceptions.RequestException as e:
            logging.error(f"Error de conexión con ElevenLabs: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logging.error("ElevenLabs devolvió HTTP %s", e.response.status_code)
            return None
        except Exception as e:
            logging.error(f"Error transcribiendo {audio_file_path} con ElevenLabs: {e}")
            return None


class LocalWhisperTranscriptionService(TranscriptionService):
    """Servicio de transcripcion local basado en faster-whisper."""

    _PUNCTUATION_PREFIXES = tuple(",.;:!?)]}%")

    def __init__(self, model_size: str = "base", device: str = "auto"):
        super().__init__()
        self.model_size = (model_size or "base").strip()
        self.requested_device = (device or "auto").strip().lower()
        self.device = self.requested_device
        self.models_dir = _get_models_dir()
        self._model: Any = None
        self._model_device = self.device
        self._model_compute_type = ""
        self._model_lock = threading.Lock()

    def _load_model(self) -> Any:
        """Carga el modelo local bajo demanda."""
        if self._model is not None:
            return self._model

        with self._model_lock:
            if self._model is not None:
                return self._model

            self.models_dir.mkdir(parents=True, exist_ok=True)
            logging.info(
                "Cargando modelo local faster-whisper '%s' en %s",
                self.model_size,
                self.models_dir,
            )
            target_device = self._resolve_target_device()

            try:
                self._model = self._create_model(target_device)
                self._model_device = target_device
            except ImportError as exc:
                raise RuntimeError(
                    "faster-whisper no esta instalado. "
                    "Instala la dependencia antes de usar el modo local."
                ) from exc
            except Exception as exc:
                if target_device == "cuda" and self._should_fallback_to_cpu(exc):
                    logging.warning(
                        "No se pudo inicializar faster-whisper con '%s'. "
                        "Se reintentara en CPU: %s",
                        target_device,
                        exc,
                    )
                    self._model = self._create_model("cpu")
                    self._model_device = "cpu"
                else:
                    raise RuntimeError(
                        "No se pudo cargar el modelo local faster-whisper. "
                        "Es posible que falte memoria, conectividad para la descarga "
                        "inicial o algun runtime de CTranslate2/CUDA."
                    ) from exc

        return self._model

    def _resolve_target_device(self) -> str:
        """Resuelve el dispositivo real a intentar al cargar el modelo."""
        if self.device == "auto":
            return "cuda"
        return self.device

    def _create_model(self, device: str) -> Any:
        """Crea una instancia de WhisperModel."""
        _register_windows_cuda_runtime()
        from faster_whisper import WhisperModel

        compute_type = "int8" if device == "cpu" else "float16"
        cpu_threads = max(1, min(os.cpu_count() or 1, 8))
        self._model_compute_type = compute_type

        return WhisperModel(
            self.model_size,
            device=device,
            compute_type=compute_type,
            cpu_threads=cpu_threads,
            num_workers=1,
            download_root=str(self.models_dir),
        )

    @staticmethod
    def _should_fallback_to_cpu(exc: Exception) -> bool:
        """Indica si un error de inicializacion merece fallback a CPU."""
        message = str(exc).lower()
        fallback_markers = (
            "cuda",
            "cublas",
            "cudnn",
            "not compiled with cuda support",
            "failed to create cuda device",
            "cannot be loaded",
        )
        return any(marker in message for marker in fallback_markers)

    def _switch_to_cpu(self) -> Any:
        """Reinicializa el modelo en CPU tras un fallo de CUDA."""
        with self._model_lock:
            self.device = "cpu"
            self._model = None
            self._model_device = "cpu"
        return self._load_model()

    def _build_run_metadata(self) -> Dict[str, Any]:
        """Construye metadatos verificables del backend local usado."""
        effective_device = self._model_device or "desconocido"
        execution_target = "GPU" if effective_device == "cuda" else "CPU"
        return {
            "service_type": "local",
            "service_name": "Modelo local (Faster-Whisper)",
            "provider": "faster-whisper",
            "mode": "local",
            "model": self.model_size,
            "model_identifier": f"Systran/faster-whisper-{self.model_size}",
            "requested_device": self.requested_device,
            "effective_device": effective_device,
            "execution_target": execution_target,
            "compute_type": self._model_compute_type or "desconocido",
        }

    @classmethod
    def _merge_segments(cls, segments: list[str]) -> str:
        """Concatena segmentos preservando la puntuacion final."""
        merged: list[str] = []
        for fragment in segments:
            text = fragment.strip()
            if not text:
                continue
            if merged and text.startswith(cls._PUNCTUATION_PREFIXES):
                merged[-1] = f"{merged[-1]}{text}"
                continue
            merged.append(text)
        return " ".join(merged).strip()

    def transcribe(self, audio_file_path: str, language: str = "es") -> Optional[str]:
        """Transcribe audio localmente usando faster-whisper."""
        try:
            if not Path(audio_file_path).is_file():
                raise FileNotFoundError(
                    f"No existe el archivo de audio: {audio_file_path}"
                )

            model = self._load_model()
            logging.info(
                "Transcribiendo localmente con faster-whisper (%s, device=%s): %s",
                self.model_size,
                self._model_device,
                audio_file_path,
            )

            try:
                segments, _info = model.transcribe(
                    audio_file_path,
                    language=language or None,
                    task="transcribe",
                    beam_size=5,
                )
                segment_texts = [
                    segment.text
                    for segment in segments
                    if getattr(segment, "text", None)
                ]
            except Exception as exc:
                if self.device in {"auto", "cuda"} and self._should_fallback_to_cpu(exc):
                    logging.warning(
                        "Fallo de CUDA al transcribir con faster-whisper. "
                        "Se reintentara en CPU: %s",
                        exc,
                    )
                    model = self._switch_to_cpu()
                    segments, _info = model.transcribe(
                        audio_file_path,
                        language=language or None,
                        task="transcribe",
                        beam_size=5,
                    )
                    segment_texts = [
                        segment.text
                        for segment in segments
                        if getattr(segment, "text", None)
                    ]
                else:
                    raise

            transcript_text = self._merge_segments(segment_texts)

            if not transcript_text:
                logging.warning(
                    "La transcripcion local no produjo texto para: %s",
                    audio_file_path,
                )
                return None

            logging.info(
                "Transcripcion local completada: %s caracteres",
                len(transcript_text),
            )
            self._set_last_run_metadata(self._build_run_metadata())
            return transcript_text

        except MemoryError:
            logging.error(
                "Memoria insuficiente cargando o ejecutando faster-whisper "
                "con el modelo '%s'",
                self.model_size,
            )
            return None
        except FileNotFoundError as exc:
            logging.error("Archivo de audio no encontrado para faster-whisper: %s", exc)
            return None
        except OSError as exc:
            logging.error("Error de E/S transcribiendo con faster-whisper: %s", exc)
            return None
        except RuntimeError as exc:
            logging.error("Error de faster-whisper: %s", exc)
            return None
        except Exception as exc:
            logging.error(
                "Error inesperado transcribiendo %s con faster-whisper: %s",
                audio_file_path,
                exc,
            )
            return None


class TranscriptionServiceFactory:
    """Factory para crear servicios de transcripcion."""

    @staticmethod
    def create_service(service_type: str, config_manager) -> TranscriptionService:
        """
        Crea un servicio de transcripción según el tipo especificado
        
        Args:
            service_type: 'openai', 'elevenlabs' o 'local'
            config_manager: Gestor de configuración
            
        Returns:
            Instancia del servicio de transcripción
        """
        normalized_type = service_type.lower()

        if normalized_type == "openai":
            api_key = config_manager.get("OPENAI_API_KEY")
            if not api_key:
                return MissingConfigTranscriptionService(
                    "OPENAI_API_KEY no esta configurada. "
                    "Anadela en config.json o variable de entorno."
                )

            model = config_manager.get("WHISPER_MODEL", "whisper-1")
            return OpenAITranscriptionService(api_key, model)

        if normalized_type == "elevenlabs":
            api_key = config_manager.get("ELEVENLABS_API_KEY")
            if not api_key:
                return MissingConfigTranscriptionService(
                    "ELEVENLABS_API_KEY no esta configurada. "
                    "Anadela en config.json o variable de entorno."
                )

            return ElevenLabsTranscriptionService(api_key)

        if normalized_type == "local":
            model_size = config_manager.get("LOCAL_WHISPER_MODEL", "base")
            return LocalWhisperTranscriptionService(model_size=model_size, device="auto")

        raise ValueError(f"Tipo de servicio no soportado: {service_type}")


class TranscriptionManager:
    """Gestor principal de transcripcion que coordina el proceso."""

    def __init__(self, config_manager):
        self.config = config_manager
        self._last_run_metadata: Dict[str, Any] = {}

        # Determinar qué servicio usar basado en la configuración
        service_type = config_manager.get("TRANSCRIPTION_SERVICE", "local")
        self.service = TranscriptionServiceFactory.create_service(service_type, config_manager)
    
    def transcribe_audio_segments(self, audio_files: list, language: str = "es") -> list:
        """
        Transcribe múltiples segmentos de audio concurrentemente
        
        Args:
            audio_files: Lista de rutas de archivos de audio
            language: Código de idioma
            
        Returns:
            Lista de transcripciones en el mismo orden
        """
        transcripts = [None] * len(audio_files)
        
        def process_segment(index: int, audio_file: str):
            logging.info(f"Procesando segmento {index + 1}/{len(audio_files)}: {audio_file}")
            transcript = self.service.transcribe(audio_file, language)
            metadata = self.service.get_last_run_metadata()
            
            if transcript:
                logging.info(f"Segmento {index + 1} transcrito exitosamente")
            else:
                logging.warning(f"No se pudo transcribir el segmento {index + 1}: {audio_file}")
            
            return index, transcript, metadata

        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = [
                executor.submit(process_segment, i, f) 
                for i, f in enumerate(audio_files)
            ]
            
            for future in concurrent.futures.as_completed(futures):
                try:
                    index, transcript, metadata = future.result()
                    transcripts[index] = transcript
                    if transcript and metadata:
                        self._last_run_metadata = metadata
                except Exception as e:
                    logging.error(f"Error procesando segmento asíncrono: {e}")
        
        # Filtrar posibles fallos (None)
        return [t for t in transcripts if t is not None]
    
    def get_full_transcript(self, audio_files: list, language: str = "es") -> str:
        """
        Obtiene la transcripción completa de todos los segmentos
        
        Args:
            audio_files: Lista de rutas de archivos de audio
            language: Código de idioma
            
        Returns:
            Transcripción completa concatenada
        """
        transcripts = self.transcribe_audio_segments(audio_files, language)
        
        if not transcripts:
            raise RuntimeError("No se pudo transcribir ningún segmento de audio")
        
        full_transcript = "\n".join(transcripts)
        logging.info(f"Transcripción completa generada: {len(full_transcript)} caracteres")
        
        return full_transcript

    def get_last_run_metadata(self) -> Dict[str, Any]:
        """Devuelve metadatos del backend usado en la ultima transcripcion."""
        return dict(self._last_run_metadata)
