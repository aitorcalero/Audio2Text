"""
Aplicación principal Audio2Text refactorizada
Soporta OpenAI Whisper y ElevenLabs para transcripción
"""
import logging
import os
import sys
import tkinter as tk
from pathlib import Path
from typing import Optional
import threading
import time


def _get_appdata_dir() -> Path:
    """Devuelve el directorio de datos de aplicación, escribible en modo .exe."""
    base = os.environ.get("LOCALAPPDATA")
    if base:
        return Path(base) / "Audio2Text"
    return Path.home() / ".audio2text"


# Configurar logging en una ubicación segura
_log_dir = _get_appdata_dir() / "logs"
_log_dir.mkdir(parents=True, exist_ok=True)
_log_file = _log_dir / "audio2text.log"

logging.basicConfig(
    handlers=[
        logging.FileHandler(filename=_log_file, mode='a', encoding='utf-8'),
        logging.StreamHandler()
    ],
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Importar módulos locales
from config_manager import ConfigManager
from audio_processor import AudioProcessor
from transcription_services import TranscriptionManager
from text_processing import TextAnalysisManager
from output_manager import OutputFileManager
from gui_components import GUIManager, ProgressDialog, APIKeysDialog


class Audio2TextProcessor:
    """Procesador principal de la aplicación Audio2Text"""
    
    def __init__(self, config_file: str = "config.json"):
        """
        Inicializa el procesador
        
        Args:
            config_file: Ruta del archivo de configuración
        """
        try:
            # Cargar configuración
            self.config_manager = ConfigManager(config_file)
            logging.info("Configuración cargada exitosamente")
            
            # Verificar si faltan las claves API (Primer uso)
            openai_key = self.config_manager.get("OPENAI_API_KEY", "")
            eleven_key = self.config_manager.get("ELEVENLABS_API_KEY", "")
            
            if not openai_key and not eleven_key:
                logging.info("Claves API no encontradas. Solicitando al usuario...")
                dialog = APIKeysDialog()
                keys = dialog.show()
                if keys:
                    self.config_manager.save_config(keys)
                    logging.info("Nuevas claves API guardadas.")
                else:
                    logging.warning("El usuario canceló la introducción de claves API. La aplicación puede no funcionar correctamente.")
            
            # Inicializar componentes
            self.audio_processor = AudioProcessor(self.config_manager)
            self.transcription_manager = TranscriptionManager(self.config_manager)
            self.text_analysis_manager = TextAnalysisManager(self.config_manager)
            self.output_manager = OutputFileManager(self.config_manager)
            self.gui_manager = GUIManager(self.config_manager)
            
            logging.info("Todos los componentes inicializados correctamente")
            
        except Exception as e:
            logging.error(f"Error inicializando la aplicación: {e}")
            # Evitar fallar si la GUI aún no está disponible
            try:
                if hasattr(self, "gui_manager"):
                    self.gui_manager.show_error("Error de inicialización", str(e))
                else:
                    # Fallback simple para mostrar el error al usuario
                    from tkinter import messagebox
                    root = tk.Tk()
                    root.withdraw()
                    messagebox.showerror("Error de inicialización", str(e))
                    root.destroy()
            except Exception:
                pass
            sys.exit(1)
    
    def process_single_file(self, input_file: str, output_file: str, 
                           forced_language: Optional[str] = None, 
                           progress_callback: Optional[callable] = None) -> bool:
        """
        Procesa un archivo de audio completo
        
        Args:
            input_file: Ruta del archivo de audio de entrada
            output_file: Ruta del archivo de salida
            forced_language: Idioma forzado por el usuario (opcional)
            progress_callback: Función de callback para actualizar progreso
            
        Returns:
            True si el procesamiento fue exitoso, False en caso contrario
        """
        try:
            logging.info(f"Iniciando procesamiento de: {Path(input_file).name}")
            
            # Paso 1: Preparar segmentos de audio
            if progress_callback:
                progress_callback("Preparando segmentos de audio...")
            
            audio_segments = self.audio_processor.prepare_audio_segments(input_file)
            logging.info(f"Preparados {len(audio_segments)} segmentos de audio")
            
            # Paso 2: Transcribir audio
            if progress_callback:
                progress_callback("Transcribiendo audio...")
            
            # Determinar idioma para transcripción
            transcription_language = forced_language or self.config_manager.get('IDIOMA_FORZADO', 'es')
            
            full_transcript = self.transcription_manager.get_full_transcript(
                audio_segments, 
                transcription_language
            )
            logging.info("Transcripción completada")
            
            # Paso 3: Analizar texto y generar resúmenes
            if progress_callback:
                progress_callback("Analizando texto y generando resúmenes...")
            
            analysis_result = self.text_analysis_manager.process_transcript(
                full_transcript, 
                forced_language
            )
            logging.info("Análisis de texto completado")
            
            # Paso 4: Guardar resultados
            if progress_callback:
                progress_callback("Guardando resultados...")
            
            success = self.output_manager.save_transcription(output_file, analysis_result)
            
            if success:
                logging.info(f"Procesamiento completado exitosamente: {Path(output_file).name}")
                
                # Abrir archivo de salida
                self.output_manager.open_output_file(output_file)
                
                # Limpiar archivos temporales
                self.audio_processor.cleanup_temporary_files(audio_segments, input_file)
                
                return True
            else:
                logging.error("Error guardando los resultados")
                return False
                
        except Exception as e:
            logging.error(f"Error procesando archivo {input_file}: {e}")
            self.gui_manager.show_error("Error de procesamiento", str(e))
            return False
        
        finally:
            # Asegurar limpieza de archivos temporales
            try:
                if 'audio_segments' in locals():
                    self.audio_processor.cleanup_temporary_files(audio_segments, input_file)
            except Exception as cleanup_error:
                logging.warning(f"Error en limpieza: {cleanup_error}")
    
    def process_with_gui(self):
        """Procesa archivos con interfaz gráfica"""
        logging.info("Iniciando interfaz gráfica...")
        try:
            while True:
                logging.info("Mostrando diálogo de selección de servicio...")
                # Seleccionar servicio de transcripción
                selected_service = self.gui_manager.select_transcription_service()
                logging.info(f"Usuario seleccionó: {selected_service}")
                
                if not selected_service:
                    logging.info("Selección de servicio cancelada por el usuario")
                    break
                
                # Actualizar configuración con el servicio seleccionado
                if selected_service != self.config_manager.get('TRANSCRIPTION_SERVICE'):
                    logging.info(f"Cambiando servicio de transcripción a: {selected_service}")
                    self.config_manager.config['TRANSCRIPTION_SERVICE'] = selected_service
                    
                    # Recrear el gestor de transcripción con el nuevo servicio
                    self.transcription_manager = TranscriptionManager(self.config_manager)
                
                # Obtener archivos del usuario
                input_file, output_file = self.gui_manager.get_user_files()
                
                if not input_file or not output_file:
                    logging.info("Selección de archivos cancelada por el usuario")
                    break
                
                # Preguntar por idioma forzado
                forced_language = self.gui_manager.ask_force_language()
                
                # Crear diálogo de progreso
                progress_dialog = ProgressDialog(None, "Procesando archivo de audio...")
                
                def update_progress(message: str):
                    try:
                        progress_dialog.update_status(message)
                        if progress_dialog.cancelled:
                            raise InterruptedError("Procesamiento cancelado por el usuario")
                    except tk.TclError:
                        pass
                
                result = {"success": None, "error": None, "cancelled": False}
                
                def worker():
                    try:
                        service_name = "OpenAI Whisper" if selected_service == "openai" else "ElevenLabs"
                        update_progress(f"Usando {service_name} para transcripción...")
                        
                        start_time = time.time()
                        success = self.process_single_file(
                            input_file,
                            output_file,
                            forced_language,
                            update_progress
                        )
                        end_time = time.time()
                        
                        result["success"] = success
                        result["elapsed"] = end_time - start_time
                        
                    except InterruptedError:
                        result["cancelled"] = True
                    except Exception as e:
                        result["error"] = str(e)
                
                thread = threading.Thread(target=worker, daemon=True)
                thread.start()
                
                def poll():
                    if thread.is_alive():
                        try:
                            progress_dialog.root.after(200, poll)
                        except tk.TclError:
                            pass
                        return
                    
                    # Thread terminado
                    progress_dialog.close()
                    
                    if result["cancelled"]:
                        logging.info("Procesamiento cancelado por el usuario")
                        return
                    
                    if result["error"]:
                        logging.error(f"Error durante el procesamiento: {result['error']}")
                        self.gui_manager.show_error("Error", result["error"])
                        return
                    
                    if result["success"]:
                        elapsed_time = result.get("elapsed", 0)
                        minutes = int(elapsed_time // 60)
                        seconds = int(elapsed_time % 60)
                        
                        self.gui_manager.show_info(
                            "Procesamiento completado",
                            f"El archivo se ha procesado exitosamente en {minutes}m {seconds}s.\n\n"
                            f"Resultado guardado en:\n{output_file}"
                        )
                    else:
                        self.gui_manager.show_error(
                            "Error de procesamiento",
                            "No se pudo completar el procesamiento del archivo."
                        )
                
                poll()
                try:
                    progress_dialog.root.mainloop()
                except tk.TclError:
                    pass
                
                if not result.get("success"):
                    # No preguntar continuar si falló o canceló
                    if result.get("cancelled"):
                        continue
                    # Si hubo error, seguir al loop para reintentar/terminar
                    if not self.gui_manager.ask_continue_processing():
                        break
                else:
                    if not self.gui_manager.ask_continue_processing():
                        break
        
        except Exception as e:
            logging.error(f"Error en la interfaz gráfica: {e}")
            self.gui_manager.show_error("Error de aplicación", str(e))
    
    def process_command_line(self, input_file: str, output_file: str, 
                           forced_language: Optional[str] = None):
        """
        Procesa archivos desde línea de comandos
        
        Args:
            input_file: Archivo de entrada
            output_file: Archivo de salida
            forced_language: Idioma forzado
        """
        def print_progress(message: str):
            logging.info(f"[PROGRESO] {message}")
        
        success = self.process_single_file(
            input_file, 
            output_file, 
            forced_language,
            print_progress
        )
        
        if success:
            logging.info(f"Procesamiento completado: {output_file}")
        else:
            logging.error("Error en el procesamiento")
            sys.exit(1)


def main():
    """Función principal"""
    try:
        logging.info("Inicializando Audio2Text...")
        
        # Inicializar procesador
        processor = Audio2TextProcessor()
        
        logging.info(f"Argumentos recibidos: {sys.argv}")
        logging.info(f"Número de argumentos: {len(sys.argv)}")
        
        # Verificar argumentos de línea de comandos
        if len(sys.argv) >= 3:
            logging.info("Ejecutando en modo línea de comandos...")
            # Modo línea de comandos
            input_file = sys.argv[1]
            output_file = sys.argv[2]
            forced_language = sys.argv[3] if len(sys.argv) > 3 else None
            
            processor.process_command_line(input_file, output_file, forced_language)
        else:
            logging.info("Ejecutando en modo interfaz gráfica...")
            # Modo interfaz gráfica
            processor.process_with_gui()
    
    except KeyboardInterrupt:
        logging.info("Aplicación interrumpida por el usuario")
    except Exception as e:
        logging.error(f"Error fatal en la aplicación: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
