"""
Gestor de configuración para la aplicación Audio2Text
"""
import json
import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, List


def _get_base_path() -> Path:
    """
    Devuelve la ruta base del bundle. Compatible con PyInstaller (sys._MEIPASS).
    """
    if getattr(sys, "_MEIPASS", None):
        return Path(sys._MEIPASS)  # type: ignore[attr-defined]
    return Path(__file__).resolve().parent


class ConfigManager:
    """Maneja la configuración de la aplicación"""
    MAX_CONFIG_SIZE_BYTES = 1024 * 1024
    
    def __init__(self, config_file: str = "config.json"):
        self.config_file = config_file
        self.config = self._load_config()
        self._validate_config()
    
    def _candidate_paths(self) -> List[Path]:
        """
        Posibles ubicaciones para el archivo de configuración.
        1) Ruta explícita por variable de entorno AUDIO2TEXT_CONFIG
        2) Directorio actual / junto al exe
        3) Directorio del bundle (PyInstaller) o del módulo
        4) %LOCALAPPDATA%/Audio2Text/config.json
        """
        candidates: List[Path] = []
        
        env_config = os.environ.get("AUDIO2TEXT_CONFIG")
        if env_config:
            candidates.append(Path(env_config))
        
        # Config en cwd o junto al ejecutable
        candidates.append(Path(self.config_file).expanduser())
        
        # Config junto al bundle / módulo
        candidates.append(_get_base_path() / self.config_file)
        
        # Config en AppData local (Windows)
        local_appdata = os.environ.get("LOCALAPPDATA")
        if local_appdata:
            candidates.append(Path(local_appdata) / "Audio2Text" / self.config_file)
        
        return candidates
    
    def _load_config(self) -> Dict[str, Any]:
        """Carga la configuración desde el archivo JSON o usa valores por defecto."""
        default_config: Dict[str, Any] = {
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
            "SUMMARY_TEMPERATURE": 0.3,
        }
        
        for path in self._candidate_paths():
            try:
                if path.exists():
                    if not self._is_supported_config_path(path):
                        continue
                    data = self._load_json_config(path)
                    logging.info("Configuración cargada desde: %s", path)
                    default_config.update(data or {})
                    return default_config
            except json.JSONDecodeError as e:
                logging.error(f"Error al parsear el archivo de configuración ({path.name}): {e}")
                break  # No seguir buscando si el archivo existe pero está corrupto
            except ValueError as e:
                logging.error(f"Configuración inválida en {path.name}: {e}")
                break
            except Exception as e:
                logging.error(f"No se pudo leer la configuración en {path.name}: {e}")
                continue
        
        logging.warning(f"Usando configuración por defecto al no encontrar {self.config_file}")
        return default_config

    def _is_supported_config_path(self, path: Path) -> bool:
        """
        Acepta solo archivos JSON pequeños. Esto evita intentar leer binarios
        o archivos enormes como si fueran configuración de texto.
        """
        if not path.is_file():
            logging.warning(f"Se omite {path.name}: no es un archivo regular")
            return False

        if path.suffix.lower() != ".json":
            logging.warning(f"Se omite {path.name}: extensión no soportada para configuración")
            return False

        size_bytes = path.stat().st_size
        if size_bytes > self.MAX_CONFIG_SIZE_BYTES:
            logging.warning(
                "Se omite %s: tamaño %s bytes supera el máximo permitido de %s bytes",
                path.name,
                size_bytes,
                self.MAX_CONFIG_SIZE_BYTES,
            )
            return False

        return True

    def _load_json_config(self, path: Path) -> Dict[str, Any]:
        """Carga un archivo JSON de configuración ya validado."""
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, dict):
            raise ValueError("el archivo debe contener un objeto JSON")

        return data
    
    def _validate_config(self):
        """
        Valida que las claves generales estén presentes.
        Las API keys se validan al crear cada servicio concreto.
        """
        required_keys = [
            "FILE_SIZE_LIMIT_MB",
            "CHUNK_DURATION_MIN",
            "TRANSCRIPTION_SERVICE",
        ]
        
        missing_keys = [key for key in required_keys if key not in self.config]
        if missing_keys:
            raise ValueError(f"Faltan las siguientes claves en la configuración: {missing_keys}")
            
    def save_config(self, new_config: dict = None) -> bool:
        """
        Guarda la configuración actual (o una nueva proporcionada) en el archivo de configuración.
        Intenta guardarla preferentemente en AppData para permisos de escritura desde .exe.
        """
        if new_config:
            self.config.update(new_config)

        candidate_paths: List[Path] = []
        env_config = os.environ.get("AUDIO2TEXT_CONFIG")
        if env_config:
            candidate_paths.append(Path(env_config).expanduser())

        local_appdata = os.environ.get("LOCALAPPDATA")
        if local_appdata:
            candidate_paths.append(Path(local_appdata) / "Audio2Text" / self.config_file)
        else:
            candidate_paths.append(Path.home() / ".audio2text" / self.config_file)

        last_error: Exception | None = None
        for save_path in candidate_paths:
            try:
                save_path.parent.mkdir(parents=True, exist_ok=True)
                with open(save_path, "w", encoding="utf-8") as f:
                    json.dump(self.config, f, indent=4, ensure_ascii=False)
                logging.info(f"Configuración guardada en: {save_path}")
                return True
            except Exception as e:
                last_error = e
                logging.error(
                    "No se pudo guardar la configuración en %s: %s",
                    save_path,
                    e,
                )

        if last_error:
            logging.error("No se pudo guardar la configuración en ninguna ubicación candidata")
        return False
    
    def get(self, key: str, default=None):
        """Obtiene un valor de configuración"""
        return self.config.get(key, default)
    
    def get_int(self, key: str, default: int = 0) -> int:
        """Obtiene un valor entero de configuración"""
        return int(self.config.get(key, default))
    
    def get_float(self, key: str, default: float = 0.0) -> float:
        """Obtiene un valor flotante de configuración"""
        return float(self.config.get(key, default))
    
    def get_bool(self, key: str, default: bool = False) -> bool:
        """Obtiene un valor booleano de configuración"""
        value = self.config.get(key, default)
        if isinstance(value, str):
            return value.lower() in ("true", "1", "yes", "on")
        return bool(value)

