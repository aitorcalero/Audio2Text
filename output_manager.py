"""
Gestor de archivos de salida para la aplicación Audio2Text
"""
import os
import logging
from datetime import datetime
from typing import Dict, Any, Optional


class OutputFileManager:
    """Maneja la creación y guardado de archivos de salida"""
    
    def __init__(self, config_manager):
        self.config = config_manager
    
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
        
        # Crear encabezado
        header = f"""# Transcripción de Audio - Audio2Text
**Fecha:** {timestamp}
**Idioma detectado:** {language}
**Partes procesadas:** {analysis_result.get('text_parts_count', 0)}
**Resúmenes generados:** {analysis_result.get('summaries_count', 0)}

---

"""
        
        # Sección de resumen
        summary_section = f"""## Resumen

{final_summary}

---

"""
        
        # Sección de transcripción completa
        transcript_section = f"""## Transcripción Original

{original_transcript}

---

*Generado por Audio2Text*
"""
        
        return header + summary_section + transcript_section
    
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
            content = self.create_output_content(analysis_result)
            
            # Asegurar que el directorio existe
            output_dir = os.path.dirname(output_file)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            # Guardar archivo
            with open(output_file, "w", encoding='utf-8') as f:
                f.write(content)
            
            logging.info(f"Archivo guardado exitosamente: {output_file}")
            return True
            
        except Exception as e:
            logging.error(f"Error guardando archivo {output_file}: {e}")
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
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            content = f"""# Transcripción de Audio - Audio2Text (En progreso)
**Última actualización:** {timestamp}
{progress_info}

---

## Resumen (Parcial)

{partial_summary}

---

## Transcripción Original

{full_transcript}

---

*Generado por Audio2Text (Procesamiento en curso)*
"""
            
            with open(output_file, "w", encoding='utf-8') as f:
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
            if os.path.exists(output_file):
                os.startfile(output_file)
                logging.info(f"Archivo abierto: {output_file}")
            else:
                logging.warning(f"Archivo no encontrado: {output_file}")
        except Exception as e:
            logging.warning(f"No se pudo abrir automáticamente el archivo {output_file}: {e}")
    
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