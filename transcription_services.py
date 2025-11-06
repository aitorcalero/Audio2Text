"""
Servicios de transcripción para la aplicación Audio2Text
Soporta OpenAI Whisper y ElevenLabs
"""
import openai
import logging
from typing import Optional, Protocol
from abc import ABC, abstractmethod
import requests
import json


class TranscriptionService(ABC):
    """Interfaz abstracta para servicios de transcripción"""
    
    @abstractmethod
    def transcribe(self, audio_file_path: str, language: str = "es") -> Optional[str]:
        """Transcribe un archivo de audio a texto"""
        pass


class OpenAITranscriptionService(TranscriptionService):
    """Servicio de transcripción usando OpenAI Whisper"""
    
    def __init__(self, api_key: str, model: str = "whisper-1"):
        self.api_key = api_key
        self.model = model
        
        # Configurar el cliente OpenAI según la versión
        try:
            # Para OpenAI >= 1.0.0
            from openai import OpenAI
            self.client = OpenAI(api_key=api_key)
            self.is_new_api = True
        except ImportError:
            # Para OpenAI < 1.0.0 (API antigua)
            import openai
            openai.api_key = api_key
            self.client = openai
            self.is_new_api = False
    
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
                if self.is_new_api:
                    # Nueva API (>= 1.0.0)
                    transcript = self.client.audio.transcriptions.create(
                        model=self.model,
                        file=audio_file,
                        language=language
                    )
                    text_result = transcript.text
                else:
                    # API antigua (< 1.0.0)
                    transcript = self.client.Audio.transcribe(
                        self.model, 
                        audio_file, 
                        language=language
                    )
                    text_result = transcript.text
            
            logging.info(f"Transcripción completada: {len(text_result)} caracteres")
            return text_result
            
        except Exception as e:
            logging.error(f"Error transcribiendo {audio_file_path} con OpenAI: {e}")
            return None


class ElevenLabsTranscriptionService(TranscriptionService):
    """Servicio de transcripción usando ElevenLabs"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.elevenlabs.io/v1"
    
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
            
            # ElevenLabs acepta diferentes formatos de audio
            with open(audio_file_path, "rb") as audio_file:
                files = {
                    "audio": audio_file,
                }
                data = {
                    "language": language,
                    "model_id": "eleven_multilingual_v2"  # Modelo multiidioma de ElevenLabs
                }
                
                response = requests.post(url, headers=headers, files=files, data=data)
                response.raise_for_status()
            
            result = response.json()
            transcript_text = result.get("text", "")
            
            logging.info(f"Transcripción completada con ElevenLabs: {len(transcript_text)} caracteres")
            return transcript_text
            
        except requests.exceptions.RequestException as e:
            logging.error(f"Error de conexión con ElevenLabs: {e}")
            return None
        except Exception as e:
            logging.error(f"Error transcribiendo {audio_file_path} con ElevenLabs: {e}")
            return None


class TranscriptionServiceFactory:
    """Factory para crear servicios de transcripción"""
    
    @staticmethod
    def create_service(service_type: str, config_manager) -> TranscriptionService:
        """
        Crea un servicio de transcripción según el tipo especificado
        
        Args:
            service_type: 'openai' o 'elevenlabs'
            config_manager: Gestor de configuración
            
        Returns:
            Instancia del servicio de transcripción
        """
        if service_type.lower() == "openai":
            api_key = config_manager.get("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY no está configurado")
            
            model = config_manager.get("WHISPER_MODEL", "whisper-1")
            return OpenAITranscriptionService(api_key, model)
        
        elif service_type.lower() == "elevenlabs":
            api_key = config_manager.get("ELEVENLABS_API_KEY")
            if not api_key:
                raise ValueError("ELEVENLABS_API_KEY no está configurado")
            
            return ElevenLabsTranscriptionService(api_key)
        
        else:
            raise ValueError(f"Tipo de servicio no soportado: {service_type}")


class TranscriptionManager:
    """Gestor principal de transcripción que coordina el proceso"""
    
    def __init__(self, config_manager):
        self.config = config_manager
        
        # Determinar qué servicio usar basado en la configuración
        service_type = config_manager.get("TRANSCRIPTION_SERVICE", "openai")
        self.service = TranscriptionServiceFactory.create_service(service_type, config_manager)
    
    def transcribe_audio_segments(self, audio_files: list, language: str = "es") -> list:
        """
        Transcribe múltiples segmentos de audio
        
        Args:
            audio_files: Lista de rutas de archivos de audio
            language: Código de idioma
            
        Returns:
            Lista de transcripciones
        """
        transcripts = []
        
        for i, audio_file in enumerate(audio_files, 1):
            logging.info(f"Procesando segmento {i}/{len(audio_files)}: {audio_file}")
            
            transcript = self.service.transcribe(audio_file, language)
            
            if transcript:
                transcripts.append(transcript)
                logging.info(f"Segmento {i} transcrito exitosamente")
            else:
                logging.warning(f"No se pudo transcribir el segmento {i}: {audio_file}")
                # Continuar con el siguiente segmento
        
        return transcripts
    
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