"""
Gestor de archivos de salida para la aplicación Audio2Text
"""
import os
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional


class OutputFileManager:
    """Maneja la creación y guardado de archivos de salida"""

    ALLOWED_OUTPUT_EXTENSIONS = {".txt", ".md"}
    SUMMARY_LABELS = (
        "resumen",
        "summary",
        "résumé",
        "zusammenfassung",
        "riassunto",
    )
    
    def __init__(self, config_manager):
        self.config = config_manager

    def _validate_output_path(self, output_file: str) -> Path:
        """Valida que la salida apunte a un formato de texto seguro."""
        output_path = Path(output_file)
        if output_path.suffix.lower() not in self.ALLOWED_OUTPUT_EXTENSIONS:
            raise ValueError("Solo se permite guardar salidas con extensión .txt o .md")
        return output_path
    
    def create_output_content(self, analysis_result: Dict[str, Any]) -> str:
        """
        Crea el contenido del archivo de salida
        
        Args:
            analysis_result: Diccionario con los resultados del análisis
            
        Returns:
            Contenido formateado para el archivo de salida
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        language = analysis_result.get('language', 'desconocido')
        final_summary = analysis_result.get('final_summary', '')
        original_transcript = analysis_result.get('original_transcript', '')
        transcription_metadata = dict(analysis_result.get("transcription_metadata", {}))
        fallback_elapsed_seconds = analysis_result.get("transcription_elapsed_seconds")
        if (
            "elapsed_seconds" not in transcription_metadata
            and isinstance(fallback_elapsed_seconds, (int, float))
        ):
            transcription_metadata["elapsed_seconds"] = float(fallback_elapsed_seconds)
        metadata_section = self._format_transcription_metadata(transcription_metadata)
        cleaned_summary = self._clean_summary_text(final_summary, original_transcript)
        cleaned_transcript = self._normalize_block_text(original_transcript)
        
        # Crear encabezado
        header = f"""# Transcripción de Audio - Audio2Text
**Fecha:** {timestamp}
**Idioma detectado:** {language}
**Partes procesadas:** {analysis_result.get('text_parts_count', 0)}
**Resúmenes generados:** {analysis_result.get('summaries_count', 0)}
{metadata_section}

---

"""
        
        # Sección de resumen
        summary_section = f"""## Resumen

{cleaned_summary}

## Transcripción Original

~~~text
{cleaned_transcript}
~~~

---

*Generado por Audio2Text*
"""

        return header + summary_section

    def _format_transcription_metadata(self, metadata: Dict[str, Any]) -> str:
        """Formatea información del backend de transcripción usado."""
        if not metadata:
            return "**Servicio de transcripción:** Desconocido"

        lines = [
            f"**Servicio de transcripción:** {metadata.get('service_name', 'Desconocido')}",
            f"**Proveedor / motor:** {metadata.get('provider', 'Desconocido')}",
            f"**Modelo usado:** {metadata.get('model_identifier', metadata.get('model', 'Desconocido'))}",
            f"**Tipo de ejecución:** {metadata.get('execution_target', 'Desconocido')}",
        ]

        effective_device = metadata.get("effective_device")
        requested_device = metadata.get("requested_device")
        compute_type = metadata.get("compute_type")
        elapsed_seconds = metadata.get("elapsed_seconds")

        if requested_device:
            lines.append(f"**Dispositivo solicitado:** {requested_device}")
        if effective_device and effective_device != "online":
            lines.append(f"**Dispositivo efectivo:** {effective_device}")
        if compute_type:
            lines.append(f"**Precisión / compute type:** {compute_type}")
        if isinstance(elapsed_seconds, (int, float)) and elapsed_seconds >= 0:
            lines.append(
                f"**Tiempo de transcripción:** {self._format_elapsed_time(float(elapsed_seconds))}"
            )

        return "\n".join(lines)

    @staticmethod
    def _format_elapsed_time(elapsed_seconds: float) -> str:
        """Convierte segundos a un formato legible para el documento final."""
        total_seconds = max(0.0, elapsed_seconds)
        minutes, seconds = divmod(total_seconds, 60)
        hours, minutes = divmod(int(minutes), 60)

        if hours:
            return f"{hours}h {minutes:02d}m {seconds:04.1f}s"
        if minutes:
            return f"{int(minutes)}m {seconds:04.1f}s"
        return f"{seconds:.1f}s"

    def _normalize_block_text(self, text: str) -> str:
        """Normaliza el texto para su salida manteniendo su contenido."""
        cleaned = (text or "").replace("\r\n", "\n").strip()
        return cleaned or "(sin contenido)"

    def _build_transcript_probe(self, transcript: str, words: int = 14) -> str:
        """Extrae una frase inicial de la transcripción para detectar arrastre."""
        normalized = re.sub(r"\s+", " ", (transcript or "")).strip()
        if not normalized:
            return ""
        parts = normalized.split(" ")
        probe = " ".join(parts[:words]).strip()
        return probe if len(probe) >= 24 else normalized[:48]

    def _clean_summary_text(self, summary: str, transcript: str) -> str:
        """Limpia el resumen y corta texto de transcripción añadido por error."""
        cleaned = self._normalize_block_text(summary)
        cleaned = re.sub(r"^```[\w-]*\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
        cleaned = re.sub(
            rf"^\s*#+\s*(?:{'|'.join(self.SUMMARY_LABELS)})\s*:?\s*",
            "",
            cleaned,
            flags=re.IGNORECASE,
        )
        cleaned = re.sub(
            rf"^\s*(?:{'|'.join(self.SUMMARY_LABELS)})\s*:\s*",
            "",
            cleaned,
            flags=re.IGNORECASE,
        )

        transcript_probe = self._build_transcript_probe(transcript)
        if transcript_probe:
            pattern = r"\b" + r"\s+".join(
                re.escape(word) for word in transcript_probe.split()
            ) + r"\b"
            match = re.search(pattern, cleaned, flags=re.IGNORECASE)
            if match and match.start() > 20:
                cleaned = cleaned[:match.start()].rstrip(" \n:-")

        cleaned = self._collapse_duplicate_placeholder_lines(cleaned)
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()
        return cleaned or "No se pudo generar resumen."

    @staticmethod
    def _collapse_duplicate_placeholder_lines(text: str) -> str:
        """Reduce placeholders repetidos a una sola línea."""
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        if len(lines) <= 1:
            return text

        first_line = lines[0].lower()
        placeholder_prefixes = (
            "resumen no generado",
            "error generando resumen",
            "no se pudo generar resumen",
            "cliente openai no disponible",
            "falta openai_api_key",
            "no generado (falta openai_api_key)",
        )
        if all(line.lower() == first_line for line in lines) and any(
            first_line.startswith(prefix) for prefix in placeholder_prefixes
        ):
            return lines[0]

        return text
    
    def save_transcription(self, output_file: str, analysis_result: Dict[str, Any]) -> bool:
        """
        Guarda la transcripción y resumen en un archivo
        
        Args:
            output_file: Ruta del archivo de salida
            analysis_result: Diccionario con los resultados del análisis
            
        Returns:
            True si se guardó correctamente, False en caso contrario
        """
        try:
            output_path = self._validate_output_path(output_file)
            content = self.create_output_content(analysis_result)
            
            # Asegurar que el directorio existe
            output_dir = os.path.dirname(str(output_path))
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            # Guardar archivo
            with open(output_path, "w", encoding='utf-8') as f:
                f.write(content)
            
            logging.info(f"Archivo guardado exitosamente: {output_path.name}")
            return True
            
        except Exception as e:
            logging.error(f"Error guardando archivo de salida: {e}")
            return False
    
    def save_intermediate_results(self, output_file: str, partial_summary: str, 
                                  full_transcript: str, progress_info: str = "") -> bool:
        """
        Guarda resultados intermedios durante el procesamiento
        
        Args:
            output_file: Ruta del archivo de salida
            partial_summary: Resumen parcial hasta el momento
            full_transcript: Transcripción completa
            progress_info: Información del progreso
            
        Returns:
            True si se guardó correctamente, False en caso contrario
        """
        try:
            output_path = self._validate_output_path(output_file)
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            content = f"""# Transcripción de Audio - Audio2Text (En progreso)
**Última actualización:** {timestamp}
{progress_info}

---

## Resumen (Parcial)

{self._clean_summary_text(partial_summary, full_transcript)}

## Transcripción Original

~~~text
{self._normalize_block_text(full_transcript)}
~~~

---

*Generado por Audio2Text (Procesamiento en curso)*
"""
            
            with open(output_path, "w", encoding='utf-8') as f:
                f.write(content)
            
            return True
            
        except Exception as e:
            logging.error(f"Error guardando resultados intermedios: {e}")
            return False
    
    def open_output_file(self, output_file: str):
        """
        Abre el archivo de salida con la aplicación predeterminada del sistema
        
        Args:
            output_file: Ruta del archivo a abrir
        """
        try:
            output_path = Path(output_file)
            if output_path.suffix.lower() not in self.ALLOWED_OUTPUT_EXTENSIONS:
                logging.warning(
                    "Autoapertura omitida para la extensión no permitida: %s",
                    output_path.suffix or "<sin extensión>"
                )
                return

            if output_path.exists():
                os.startfile(str(output_path))
                logging.info(f"Archivo abierto: {output_path.name}")
            else:
                logging.warning(f"Archivo no encontrado: {output_path.name}")
        except Exception as e:
            logging.warning("No se pudo abrir automáticamente el archivo de salida: %s", e)
    
    def create_backup(self, original_file: str) -> Optional[str]:
        """
        Crea una copia de respaldo de un archivo existente
        
        Args:
            original_file: Ruta del archivo original
            
        Returns:
            Ruta del archivo de respaldo o None si no se pudo crear
        """
        if not os.path.exists(original_file):
            return None
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_name = os.path.splitext(original_file)[0]
            extension = os.path.splitext(original_file)[1]
            backup_file = f"{base_name}_backup_{timestamp}{extension}"
            
            import shutil
            shutil.copy2(original_file, backup_file)
            
            logging.info(f"Copia de respaldo creada: {backup_file}")
            return backup_file
            
        except Exception as e:
            logging.error(f"Error creando copia de respaldo: {e}")
            return None
