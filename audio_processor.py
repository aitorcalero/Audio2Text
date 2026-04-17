"""
Procesador de audio para la aplicación Audio2Text
"""
import os
import sys
import logging
from pathlib import Path
from typing import List, Optional
import subprocess
from pydub import AudioSegment, effects
import pydub.utils as pydub_utils


def _get_base_path() -> Path:
    """Ruta base del bundle (PyInstaller compatible)."""
    if getattr(sys, "_MEIPASS", None):
        return Path(sys._MEIPASS)  # type: ignore[attr-defined]
    return Path(__file__).resolve().parent


class AudioProcessor:
    """Maneja el procesamiento y división de archivos de audio"""
    
    def __init__(self, config_manager):
        self.config = config_manager
        self._configure_ffmpeg()
    
    def _configure_ffmpeg(self):
        """
        Ajusta la ruta de ffmpeg para pydub. Útil cuando se distribuye como .exe.
        """
        ffmpeg_env = os.environ.get("FFMPEG_BINARY")
        bundled_ffmpeg = _get_base_path() / "ffmpeg.exe"
        exe_sibling_ffmpeg = Path(sys.executable).with_name("ffmpeg.exe")
        choco_real_ffmpeg = Path(r"C:\ProgramData\chocolatey\lib\ffmpeg\tools\ffmpeg\bin\ffmpeg.exe")
        
        try:
            if ffmpeg_env and Path(ffmpeg_env).exists():
                AudioSegment.converter = ffmpeg_env
                logging.info(f"Usando ffmpeg desde FFMPEG_BINARY: {ffmpeg_env}")
            elif exe_sibling_ffmpeg.exists():
                AudioSegment.converter = str(exe_sibling_ffmpeg)
                logging.info(f"Usando ffmpeg junto al ejecutable: {exe_sibling_ffmpeg}")
            elif bundled_ffmpeg.exists():
                AudioSegment.converter = str(bundled_ffmpeg)
                logging.info(f"Usando ffmpeg incluido: {bundled_ffmpeg}")
            elif choco_real_ffmpeg.exists():
                AudioSegment.converter = str(choco_real_ffmpeg)
                logging.info(f"Usando ffmpeg real de Chocolatey: {choco_real_ffmpeg}")
            else:
                logging.info("ffmpeg no encontrado; se usará el del sistema si está en PATH (puede mostrar consola).")
        except Exception as e:
            logging.warning(f"No se pudo configurar ffmpeg: {e}")

        # Forzar ffmpeg sin ventana de consola en Windows
        try:
            if os.name == "nt":
                original_popen = subprocess.Popen

                def quiet_popen(cmd, *args, **kwargs):
                    try:
                        cmd_text = " ".join(cmd) if isinstance(cmd, (list, tuple)) else str(cmd)
                        if "ffmpeg" in cmd_text.lower():
                            creationflags = kwargs.pop("creationflags", 0) | subprocess.CREATE_NO_WINDOW
                            si = kwargs.get("startupinfo") or subprocess.STARTUPINFO()
                            si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                            kwargs["creationflags"] = creationflags
                            kwargs["startupinfo"] = si
                    except Exception:
                        pass
                    return original_popen(cmd, *args, **kwargs)

                # Parchea tanto subprocess como la copia que usa pydub
                subprocess.Popen = quiet_popen
                pydub_utils.subprocess.Popen = quiet_popen
                logging.info("Subproceso de ffmpeg configurado para no mostrar ventana en Windows")
        except Exception as e:
            logging.warning(f"No se pudo suprimir la ventana de ffmpeg: {e}")
        
    def get_file_size_mb(self, file_path: str) -> float:
        """Obtiene el tamaño del archivo en MB"""
        size_bytes = os.path.getsize(file_path)
        return size_bytes / (1024 * 1024)
    
    def needs_splitting(self, file_path: str) -> bool:
        """Determina si el archivo necesita ser dividido"""
        size_limit_mb = self.config.get_int("FILE_SIZE_LIMIT_MB", 24)
        file_size_mb = self.get_file_size_mb(file_path)
        
        logging.info(f"Tamaño del archivo: {file_size_mb:.2f} MB, límite: {size_limit_mb} MB")
        return file_size_mb > size_limit_mb
    
    def split_audio_by_duration(self, input_file: str, chunk_duration_min: int = 10) -> Optional[List[str]]:
        """
        Divide un archivo de audio en chunks por duración
        
        Args:
            input_file: Ruta del archivo de audio a dividir
            chunk_duration_min: Duración de cada chunk en minutos
            
        Returns:
            Lista de rutas de los archivos chunk creados, o None si hay error
        """
        try:
            logging.info(f"Dividiendo audio: {input_file} en chunks de {chunk_duration_min} minutos")
            
            audio = AudioSegment.from_file(input_file)
            chunk_duration_ms = chunk_duration_min * 60 * 1000
            
            chunks = []
            for i in range(0, len(audio), chunk_duration_ms):
                chunk = audio[i:i + chunk_duration_ms]
                chunks.append(chunk)
            
            chunk_files = []
            base_name = os.path.splitext(input_file)[0]
            
            for i, chunk in enumerate(chunks):
                chunk_filename = f"{base_name}_chunk_{i:03d}.mp3"
                chunk.export(chunk_filename, format="mp3")
                chunk_files.append(chunk_filename)
                logging.info(f"Chunk creado: {chunk_filename}")
            
            logging.info(f"Audio dividido en {len(chunk_files)} chunks")
            return chunk_files
            
        except Exception as e:
            logging.error(f"Error dividiendo el audio: {e}")
            return None
    
    def prepare_audio_segments(self, input_file: str) -> List[str]:
        """
        Prepara los segmentos de audio para procesar, aplicando normalización de volumen
        
        Args:
            input_file: Ruta del archivo de audio original
            
        Returns:
            Lista de archivos de audio a procesar
        """
        if not os.path.exists(input_file):
            raise FileNotFoundError(f"Archivo de audio no encontrado: {input_file}")
            
        logging.info(f"Normalizando volumen del audio: {input_file}")
        try:
            audio = AudioSegment.from_file(input_file)
            normalized_audio = effects.normalize(audio)
            
            # Save normalized temp file
            base_name = os.path.splitext(input_file)[0]
            normalized_file = f"{base_name}_normalized.mp3"
            normalized_audio.export(normalized_file, format="mp3")
            logging.info(f"Audio normalizado guardado en: {normalized_file}")
        except Exception as e:
            logging.error(f"Error normalizando el audio: {e}. Usando original en su lugar.")
            normalized_file = input_file
        
        if self.needs_splitting(normalized_file):
            chunk_duration = self.config.get_int("CHUNK_DURATION_MIN", 10)
            chunk_files = self.split_audio_by_duration(normalized_file, chunk_duration)
            
            # Remove normalized file if we split it into multiple chunks
            if normalized_file != input_file and os.path.exists(normalized_file):
                try:
                    os.remove(normalized_file)
                except Exception as e:
                    logging.warning(f"No se pudo eliminar el archivo normalizado temporal: {e}")
            
            if chunk_files is None:
                raise RuntimeError("No se pudieron crear los chunks de audio")
            
            return chunk_files
        else:
            return [normalized_file]
    
    def cleanup_temporary_files(self, file_list: List[str], original_file: str):
        """
        Limpia los archivos temporales creados durante el procesamiento
        
        Args:
            file_list: Lista de archivos a limpiar
            original_file: Archivo original que no debe ser eliminado
        """
        for file_path in file_list:
            if file_path != original_file and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    logging.info(f"Archivo temporal eliminado: {file_path}")
                except Exception as e:
                    logging.warning(f"No se pudo eliminar {file_path}: {e}")
