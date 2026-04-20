"""
Servicios de transcripción para la aplicación Audio2Text
Soporta OpenAI Whisper y ElevenLabs
"""
import logging
import os
from typing import Optional
from abc import ABC, abstractmethod
import requests
import backoff
import concurrent.futures


class TranscriptionService(ABC):
    """Interfaz abstracta para servicios de transcripción"""
    
    @abstractmethod
    def transcribe(self, audio_file_path: str, language: str = "es") -> Optional[str]:
        """Transcribe un archivo de audio a texto"""
        pass


class MissingConfigTranscriptionService(TranscriptionService):
    """Servicio placeholder cuando faltan credenciales."""

    def __init__(self, reason: str):
        self.reason = reason

    def transcribe(self, audio_file_path: str, language: str = "es") -> Optional[str]:
        raise RuntimeError(self.reason)


class OpenAITranscriptionService(TranscriptionService):
    """Servicio de transcripción usando OpenAI Whisper"""
    
    def __init__(self, api_key: str, model: str = "whisper-1"):
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
            return text_result
            
        except Exception as e:
            logging.error(f"Error transcribiendo {audio_file_path} con OpenAI: {e}")
            return None


class ElevenLabsTranscriptionService(TranscriptionService):
    """Servicio de transcripción usando ElevenLabs"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.elevenlabs.io/v1"
    
    @backoff.on_exception(backoff.expo, (requests.exceptions.RequestException, Exception), max_tries=3)
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
                    "model_id": "scribe_v1"  # Modelo correcto de ElevenLabs
                }
                
                response = requests.post(url, headers=headers, files=files, data=data)
                
                logging.debug("ElevenLabs response status: %s", response.status_code)
                
                response.raise_for_status()
            
            result = response.json()
            transcript_text = result.get("text", "")
            
            logging.info(f"Transcripción completada con ElevenLabs: {len(transcript_text)} caracteres")
            return transcript_text
            
        except requests.exceptions.RequestException as e:
            logging.error(f"Error de conexión con ElevenLabs: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logging.error("ElevenLabs devolvió HTTP %s", e.response.status_code)
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
                return MissingConfigTranscriptionService("OPENAI_API_KEY no está configurada. Añádela en config.json o variable de entorno.")
            
            model = config_manager.get("WHISPER_MODEL", "whisper-1")
            return OpenAITranscriptionService(api_key, model)
        
        elif service_type.lower() == "elevenlabs":
            api_key = config_manager.get("ELEVENLABS_API_KEY")
            if not api_key:
                return MissingConfigTranscriptionService("ELEVENLABS_API_KEY no está configurada. Añádela en config.json o variable de entorno.")
            
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
            
            if transcript:
                logging.info(f"Segmento {index + 1} transcrito exitosamente")
            else:
                logging.warning(f"No se pudo transcribir el segmento {index + 1}: {audio_file}")
            
            return index, transcript

        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = [
                executor.submit(process_segment, i, f) 
                for i, f in enumerate(audio_files)
            ]
            
            for future in concurrent.futures.as_completed(futures):
                try:
                    index, transcript = future.result()
                    transcripts[index] = transcript
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
