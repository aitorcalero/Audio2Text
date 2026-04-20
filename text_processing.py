"""
Servicios de procesamiento de texto y resumen
"""
import openai
import logging
import re
import textwrap
from typing import List, Optional
import backoff
from langdetect import detect


class LanguageDetector:
    """Detector de idioma para el texto"""
    
    def __init__(self, config_manager):
        self.config = config_manager
        self.default_language = "es"
    
    def detect_language(self, text: str, forced_language: Optional[str] = None) -> str:
        """
        Detecta el idioma del texto
        
        Args:
            text: Texto a analizar
            forced_language: Idioma forzado por el usuario
            
        Returns:
            Código de idioma detectado
        """
        # Prioridad 1: Idioma forzado por el usuario
        if forced_language:
            logging.info(f"Idioma forzado por el usuario: {forced_language}")
            return forced_language
        
        # Prioridad 2: Idioma forzado por configuración
        forced_by_config = self.config.get('IDIOMA_FORZADO')
        if forced_by_config:
            logging.info(f"Idioma forzado por configuración: {forced_by_config}")
            return forced_by_config
        
        # Prioridad 3: Detección automática
        try:
            detected_lang = detect(text)
            logging.info(f"Idioma detectado automáticamente: {detected_lang}")
            return detected_lang
        except Exception as e:
            logging.error(f"Error detectando idioma: {e}. Usando '{self.default_language}' por defecto.")
            return self.default_language


class TextProcessor:
    """Procesador de texto que maneja división y formateo"""
    
    def __init__(self, config_manager):
        self.config = config_manager
        self.default_wrap_limit = 3000
    
    def split_text_for_processing(self, text: str) -> List[str]:
        """
        Divide el texto en chunks para procesamiento
        
        Args:
            text: Texto completo a dividir
            
        Returns:
            Lista de chunks de texto
        """
        wrap_limit = self.config.get_int('TEXT_WRAP_LIMIT', self.default_wrap_limit)
        
        # Split by common sentence delimiters to avoid cutting words/ideas mid-sentence
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        text_parts = []
        current_part = ""
        
        for sentence in sentences:
            if len(current_part) + len(sentence) <= wrap_limit:
                current_part += sentence + " "
            else:
                if current_part:
                    text_parts.append(current_part.strip())
                
                # If a single sentence is still larger than the wrap limit, fallback to textwrap for that sentence
                if len(sentence) > wrap_limit:
                    wrapped_sentences = textwrap.wrap(sentence, wrap_limit)
                    text_parts.extend(wrapped_sentences[:-1])
                    current_part = wrapped_sentences[-1] + " "
                else:
                    current_part = sentence + " "
                    
        if current_part.strip():
            text_parts.append(current_part.strip())
        
        logging.info(f"Texto dividido en {len(text_parts)} partes para procesamiento")
        return text_parts


class SummaryService:
    """Servicio de generación de resúmenes usando OpenAI"""
    LEGACY_COMPLETION_MODEL_PREFIXES = (
        "text-",
        "davinci",
        "curie",
        "babbage",
        "ada",
    )
    
    def __init__(self, config_manager):
        self.config = config_manager
        self.client = None
        self.enabled = False
        
        api_key = config_manager.get("OPENAI_API_KEY")
        if api_key:
            from openai import OpenAI
            self.client = OpenAI(api_key=api_key)
            self.enabled = True
        else:
            logging.warning("OPENAI_API_KEY no configurada. Se omite la generación de resúmenes.")
    
    def _get_prompt_template(self, language: str) -> str:
        """Obtiene la plantilla de prompt según el idioma"""
        templates = {
            'es': "Resumen:\n\n{text}\n\nResumen:",
            'en': "Summary:\n\n{text}\n\nSummary:",
            'fr': "Résumé:\n\n{text}\n\nRésumé:",
            'de': "Zusammenfassung:\n\n{text}\n\nZusammenfassung:",
            'it': "Riassunto:\n\n{text}\n\nRiassunto:"
        }
        return templates.get(language, templates['es'])

    def _should_use_chat_completions(self, engine: str) -> bool:
        """Decide el endpoint correcto según el nombre del modelo configurado."""
        normalized_engine = (engine or "").strip().lower()

        if not normalized_engine:
            return True

        if "instruct" in normalized_engine:
            return False

        if normalized_engine.startswith(self.LEGACY_COMPLETION_MODEL_PREFIXES):
            return False

        return True

    def _is_chat_endpoint_mismatch(self, error: Exception) -> bool:
        """Detecta si el modelo no es compatible con chat.completions."""
        error_message = str(error).lower()
        return (
            "not a chat model" in error_message
            or "use v1/completions" in error_message
        )

    def _is_completion_endpoint_mismatch(self, error: Exception) -> bool:
        """Detecta si el modelo no es compatible con completions."""
        error_message = str(error).lower()
        return (
            "not supported in the v1/completions endpoint" in error_message
            or "use v1/chat/completions" in error_message
        )

    def _create_chat_summary(
        self,
        engine: str,
        prompt: str,
        max_tokens: int,
        temperature: float,
    ) -> str:
        response = self.client.chat.completions.create(
            model=engine,
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens,
            temperature=temperature
        )
        return (response.choices[0].message.content or "").strip()

    def _create_completion_summary(
        self,
        engine: str,
        prompt: str,
        max_tokens: int,
        temperature: float,
    ) -> str:
        response = self.client.completions.create(
            model=engine,
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature
        )
        return response.choices[0].text.strip()
    
    @backoff.on_exception(backoff.expo, (Exception,), max_tries=3)
    def summarize_text(self, text: str, language: str) -> str:
        """
        Genera un resumen del texto usando OpenAI
        
        Args:
            text: Texto a resumir
            language: Idioma del texto
            
        Returns:
            Texto resumido
        """
        try:
            if not self.enabled or not self.client:
                return "Resumen no generado (falta OPENAI_API_KEY)"
            
            prompt_template = self._get_prompt_template(language)
            prompt = prompt_template.format(text=text)
            
            # Configuración del modelo
            engine = self.config.get('OPENAI_ENGINE', 'gpt-4o-mini')
            max_tokens = self.config.get_int('MAX_SUMMARY_TOKENS', 300)
            temperature = self.config.get_float('SUMMARY_TEMPERATURE', 0.3)
            
            use_chat_endpoint = self._should_use_chat_completions(engine)
            endpoint_name = "chat.completions" if use_chat_endpoint else "completions"

            logging.info(f"Generando resumen con {engine} usando {endpoint_name}")

            try:
                if use_chat_endpoint:
                    summary = self._create_chat_summary(
                        engine,
                        prompt,
                        max_tokens,
                        temperature,
                    )
                else:
                    summary = self._create_completion_summary(
                        engine,
                        prompt,
                        max_tokens,
                        temperature,
                    )
            except Exception as endpoint_error:
                if use_chat_endpoint and self._is_chat_endpoint_mismatch(endpoint_error):
                    logging.warning(
                        "El modelo %s rechazo chat.completions; reintentando con completions",
                        engine,
                    )
                    summary = self._create_completion_summary(
                        engine,
                        prompt,
                        max_tokens,
                        temperature,
                    )
                elif not use_chat_endpoint and self._is_completion_endpoint_mismatch(endpoint_error):
                    logging.warning(
                        "El modelo %s rechazo completions; reintentando con chat.completions",
                        engine,
                    )
                    summary = self._create_chat_summary(
                        engine,
                        prompt,
                        max_tokens,
                        temperature,
                    )
                else:
                    raise
            
            logging.info(f"Resumen generado: {len(summary)} caracteres")
            return summary
            
        except Exception as e:
            logging.error(f"Error generando resumen: {e}")
            return f"Error generando resumen: {str(e)}"
    
    def summarize_text_parts(self, text_parts: List[str], language: str) -> List[str]:
        """
        Genera resúmenes de múltiples partes de texto
        
        Args:
            text_parts: Lista de partes de texto
            language: Idioma del texto
            
        Returns:
            Lista de resúmenes
        """
        summaries = []
        
        for i, part in enumerate(text_parts, 1):
            logging.info(f"Generando resumen de la parte {i}/{len(text_parts)}")
            
            summary = self.summarize_text(part, language)
            if summary:
                summaries.append(summary)
            else:
                logging.warning(f"No se pudo generar resumen de la parte {i}")
        
        return summaries


class TextAnalysisManager:
    """Gestor principal para análisis de texto"""
    
    def __init__(self, config_manager):
        self.config = config_manager
        self.language_detector = LanguageDetector(config_manager)
        self.text_processor = TextProcessor(config_manager)
        self.summary_service = SummaryService(config_manager)
    
    def process_transcript(self, transcript: str, forced_language: Optional[str] = None) -> dict:
        """
        Procesa un transcript completo: detecta idioma, divide texto y genera resúmenes
        
        Args:
            transcript: Texto transcrito completo
            forced_language: Idioma forzado por el usuario
            
        Returns:
            Diccionario con el análisis completo
        """
        # Detectar idioma
        language = self.language_detector.detect_language(transcript, forced_language)
        
        # Dividir texto en partes procesables
        text_parts = self.text_processor.split_text_for_processing(transcript)
        
        # Generar resúmenes
        summaries = self.summary_service.summarize_text_parts(text_parts, language)
        
        # Combinar resúmenes
        final_summary = "\n".join(summaries) if summaries else "No se pudo generar resumen"
        
        return {
            'language': language,
            'text_parts_count': len(text_parts),
            'summaries_count': len(summaries),
            'final_summary': final_summary,
            'original_transcript': transcript
        }
