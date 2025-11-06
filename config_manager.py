"""
Gestor de configuración para la aplicación Audio2Text
"""
import json
import os
import logging
from typing import Dict, Any


class ConfigManager:
    """Maneja la configuración de la aplicación"""
    
    def __init__(self, config_file: str = "config.json"):
        self.config_file = config_file
        self.config = self._load_config()
        self._validate_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Carga la configuración desde el archivo JSON"""
        try:
            current_dir = os.path.dirname(os.path.realpath(__file__))
            config_path = os.path.join(current_dir, self.config_file)
            
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logging.error(f"Archivo de configuración no encontrado: {config_path}")
            raise
        except json.JSONDecodeError as e:
            logging.error(f"Error al parsear el archivo de configuración: {e}")
            raise
    
    def _validate_config(self):
        """Valida que todas las claves requeridas estén presentes"""
        required_keys = [
            'OPENAI_API_KEY',
            'ELEVENLABS_API_KEY',
            'FILE_SIZE_LIMIT_MB',
            'CHUNK_DURATION_MIN'
        ]
        
        missing_keys = [key for key in required_keys if key not in self.config]
        if missing_keys:
            raise ValueError(f"Faltan las siguientes claves en la configuración: {missing_keys}")
    
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
            return value.lower() in ('true', '1', 'yes', 'on')
        return bool(value)