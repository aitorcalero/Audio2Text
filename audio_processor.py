"""
Procesador de audio para la aplicación Audio2Text
"""
import os
import logging
from typing import List, Optional
from pydub import AudioSegment


class AudioProcessor:
    """Maneja el procesamiento y división de archivos de audio"""
    
    def __init__(self, config_manager):
        self.config = config_manager
        
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
        Prepara los segmentos de audio para procesar
        
        Args:
            input_file: Ruta del archivo de audio original
            
        Returns:
            Lista de archivos de audio a procesar
        """
        if not os.path.exists(input_file):
            raise FileNotFoundError(f"Archivo de audio no encontrado: {input_file}")
        
        if self.needs_splitting(input_file):
            chunk_duration = self.config.get_int("CHUNK_DURATION_MIN", 10)
            chunk_files = self.split_audio_by_duration(input_file, chunk_duration)
            
            if chunk_files is None:
                raise RuntimeError("No se pudieron crear los chunks de audio")
            
            return chunk_files
        else:
            return [input_file]
    
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