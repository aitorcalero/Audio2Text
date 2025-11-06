"""
Interfaz gráfica para la aplicación Audio2Text
"""
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
import sys
import logging
import threading
from typing import Optional, Callable


class ProgressDialog:
    """Diálogo de progreso para mostrar el estado del procesamiento"""
    
    def __init__(self, parent, title: str = "Procesando..."):
        self.root = tk.Toplevel(parent) if parent else tk.Tk()
        self.root.title(title)
        self.root.geometry("400x150")
        self.root.resizable(False, False)
        
        # Centrar ventana
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (400 // 2)
        y = (self.root.winfo_screenheight() // 2) - (150 // 2)
        self.root.geometry(f"+{x}+{y}")
        
        # Configurar widgets
        self.setup_widgets()
        
        # Variables
        self.cancelled = False
    
    def setup_widgets(self):
        """Configura los widgets de la ventana de progreso"""
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Etiqueta de estado
        self.status_label = ttk.Label(main_frame, text="Iniciando procesamiento...")
        self.status_label.grid(row=0, column=0, columnspan=2, pady=(0, 10))
        
        # Barra de progreso
        self.progress_bar = ttk.Progressbar(
            main_frame, 
            length=300, 
            mode='indeterminate'
        )
        self.progress_bar.grid(row=1, column=0, columnspan=2, pady=(0, 10))
        self.progress_bar.start()
        
        # Botón de cancelar
        self.cancel_button = ttk.Button(
            main_frame, 
            text="Cancelar", 
            command=self.cancel
        )
        self.cancel_button.grid(row=2, column=1, sticky=tk.E)
        
        # Configurar grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
    
    def update_status(self, message: str):
        """Actualiza el mensaje de estado"""
        try:
            if self.root and self.root.winfo_exists():
                self.status_label.config(text=message)
                self.root.update()
        except tk.TclError:
            # Ventana ya destruida
            pass
    
    def set_determinate_progress(self, maximum: int):
        """Cambia a progreso determinado"""
        try:
            if self.root and self.root.winfo_exists():
                self.progress_bar.stop()
                self.progress_bar.config(mode='determinate', maximum=maximum, value=0)
        except tk.TclError:
            # Ventana ya destruida
            pass
    
    def update_progress(self, value: int):
        """Actualiza el valor del progreso"""
        try:
            if self.root and self.root.winfo_exists():
                self.progress_bar.config(value=value)
                self.root.update()
        except tk.TclError:
            # Ventana ya destruida
            pass
    
    def cancel(self):
        """Marca el diálogo como cancelado"""
        self.cancelled = True
        self.close()
    
    def close(self):
        """Cierra la ventana de progreso"""
        try:
            if hasattr(self, 'progress_bar'):
                self.progress_bar.stop()
            if hasattr(self, 'root') and self.root:
                self.root.destroy()
        except tk.TclError:
            # Ventana ya destruida
            pass
        except Exception:
            # Cualquier otro error al cerrar
            pass


class FileSelector:
    """Manejador para selección de archivos"""
    
    @staticmethod
    def select_audio_file() -> Optional[str]:
        """
        Permite al usuario seleccionar un archivo de audio
        
        Returns:
            Ruta del archivo seleccionado o None si se canceló
        """
        file_types = [
            ("Archivos de audio", "*.mp3 *.wav *.m4a *.aac *.ogg *.flac"),
            ("MP3 files", "*.mp3"),
            ("WAV files", "*.wav"),
            ("M4A files", "*.m4a"),
            ("Todos los archivos", "*.*")
        ]
        
        file_path = filedialog.askopenfilename(
            title="Seleccione el archivo de audio",
            filetypes=file_types
        )
        
        return file_path if file_path else None
    
    @staticmethod
    def select_output_file(default_name: str = "transcription") -> Optional[str]:
        """
        Permite al usuario seleccionar dónde guardar el archivo de salida
        
        Args:
            default_name: Nombre por defecto del archivo
            
        Returns:
            Ruta del archivo de salida o None si se canceló
        """
        file_path = filedialog.asksaveasfilename(
            title="Seleccione dónde guardar la transcripción",
            defaultextension=".txt",
            initialfile=f"{default_name}.txt",
            filetypes=[
                ("Archivos de texto", "*.txt"),
                ("Archivos Markdown", "*.md"),
                ("Todos los archivos", "*.*")
            ]
        )
        
        return file_path if file_path else None


class ServiceSelectionDialog:
    """Diálogo para seleccionar el servicio de transcripción"""
    
    def __init__(self, parent, current_service: str = "openai"):
        self.parent = parent
        self.result = None
        
        # Crear ventana principal
        if parent:
            self.root = tk.Toplevel(parent)
        else:
            self.root = tk.Tk()
            
        self.root.title("Seleccionar Servicio de Transcripción")
        self.root.geometry("450x350")
        self.root.resizable(False, False)
        
        # Configurar ventana modal y traer al frente
        if parent:
            self.root.transient(parent)
            self.root.grab_set()
        
        # Centrar ventana
        self.center_window()
        
        # Configurar widgets
        self.setup_widgets(current_service)
        
        # Configurar eventos
        self.root.protocol("WM_DELETE_WINDOW", self.cancel)
        self.root.bind('<Return>', lambda e: self.accept())
        self.root.bind('<Escape>', lambda e: self.cancel())
        
        # FORZAR que la ventana aparezca al frente
        self.root.attributes('-topmost', True)  # Siempre en la parte superior
        self.root.lift()  # Traer al frente
        self.root.focus_force()  # Forzar foco
        self.root.after(100, lambda: self.root.attributes('-topmost', False))  # Quitar topmost después de un momento
    
    def center_window(self):
        """Centra la ventana en la pantalla"""
        self.root.update_idletasks()
        width = 450
        height = 350
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")
    
    def setup_widgets(self, current_service: str):
        """Configura los widgets del diálogo"""
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Título
        title_label = ttk.Label(
            main_frame,
            text="Seleccionar Servicio de Transcripción",
            font=('Arial', 12, 'bold')
        )
        title_label.pack(pady=(0, 20))
        
        # Variable para el servicio seleccionado
        self.selected_service = tk.StringVar(value=current_service)
        
        # Frame para opciones
        options_frame = ttk.LabelFrame(main_frame, text="Servicios Disponibles", padding="15")
        options_frame.pack(fill=tk.X, pady=(0, 20))
        
        # OpenAI Whisper
        openai_frame = ttk.Frame(options_frame)
        openai_frame.pack(fill=tk.X, pady=8, padx=5)
        
        self.openai_radio = ttk.Radiobutton(
            openai_frame,
            text="OpenAI Whisper",
            variable=self.selected_service,
            value="openai"
        )
        self.openai_radio.pack(side=tk.LEFT)
        
        openai_desc = ttk.Label(
            openai_frame,
            text="(Muy preciso, soporta múltiples idiomas)",
            font=('Arial', 8),
            foreground='gray'
        )
        openai_desc.pack(side=tk.LEFT, padx=(10, 0))
        
        # ElevenLabs
        elevenlabs_frame = ttk.Frame(options_frame)
        elevenlabs_frame.pack(fill=tk.X, pady=8, padx=5)
        
        self.elevenlabs_radio = ttk.Radiobutton(
            elevenlabs_frame,
            text="ElevenLabs",
            variable=self.selected_service,
            value="elevenlabs"
        )
        self.elevenlabs_radio.pack(side=tk.LEFT)
        
        elevenlabs_desc = ttk.Label(
            elevenlabs_frame,
            text="(Rápido, alta calidad de transcripción)",
            font=('Arial', 8),
            foreground='gray'
        )
        elevenlabs_desc.pack(side=tk.LEFT, padx=(10, 0))
        
        # Información adicional
        info_frame = ttk.LabelFrame(main_frame, text="Información", padding="10")
        info_frame.pack(fill=tk.X, pady=(0, 20))
        
        info_text = """• OpenAI Whisper: Excelente precisión, soporta muchos idiomas
• ElevenLabs: Procesamiento rápido, buena calidad de transcripción
• Ambos servicios requieren claves API válidas configuradas"""
        
        info_label = ttk.Label(
            info_frame,
            text=info_text,
            font=('Arial', 9),
            justify=tk.LEFT
        )
        info_label.pack(anchor=tk.W)
        
        # Botones
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.cancel_button = ttk.Button(
            button_frame,
            text="Cancelar",
            command=self.cancel
        )
        self.cancel_button.pack(side=tk.RIGHT, padx=(10, 0))
        
        self.accept_button = ttk.Button(
            button_frame,
            text="Aceptar",
            command=self.accept
        )
        self.accept_button.pack(side=tk.RIGHT)
        
        # Dar foco al botón de aceptar
        self.accept_button.focus_set()
    
    def accept(self):
        """Acepta la selección"""
        try:
            self.result = self.selected_service.get()
            logging.info(f"Usuario seleccionó servicio: {self.result}")
            self.close_dialog()
        except Exception as e:
            logging.error(f"Error al aceptar selección: {e}")
            self.result = "openai"  # Fallback
            self.close_dialog()
    
    def cancel(self):
        """Cancela la selección"""
        logging.info("Usuario canceló selección de servicio")
        self.result = None
        self.close_dialog()
    
    def close_dialog(self):
        """Cierra el diálogo de manera segura"""
        try:
            if hasattr(self, 'root') and self.root:
                if self.parent:
                    # Con parent, solo destruir
                    self.root.destroy()
                else:
                    # Sin parent, quit primero y luego destroy
                    self.root.quit()
                    self.root.destroy()
        except Exception as e:
            logging.error(f"Error cerrando diálogo: {e}")
    
    def show(self) -> Optional[str]:
        """Muestra el diálogo y retorna el servicio seleccionado"""
        try:
            # Si no hay parent, usar mainloop, si hay parent usar wait_window
            if self.parent:
                self.root.wait_window()
            else:
                self.root.mainloop()
            return self.result
        except Exception as e:
            logging.error(f"Error mostrando diálogo: {e}")
            return None


class ConfigurationDialog:
    """Diálogo para configuración de opciones"""
    
    def __init__(self, parent, current_config: dict):
        self.parent = parent
        self.result = None
        self.root = tk.Toplevel(parent) if parent else tk.Tk()
        self.root.title("Configuración")
        self.root.geometry("500x400")
        self.root.resizable(True, True)
        
        # Centrar ventana
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (500 // 2)
        y = (self.root.winfo_screenheight() // 2) - (400 // 2)
        self.root.geometry(f"+{x}+{y}")
        
        self.setup_widgets(current_config)
        self.root.transient(parent)
        self.root.grab_set()
    
    def setup_widgets(self, config: dict):
        """Configura los widgets del diálogo de configuración"""
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Pestaña de servicios
        services_frame = ttk.Frame(notebook)
        notebook.add(services_frame, text="Servicios")
        
        # Servicio de transcripción
        ttk.Label(services_frame, text="Servicio de transcripción:").pack(anchor=tk.W, pady=5)
        self.transcription_service = tk.StringVar(value=config.get('TRANSCRIPTION_SERVICE', 'openai'))
        
        transcription_frame = ttk.Frame(services_frame)
        transcription_frame.pack(fill=tk.X, pady=5)
        
        ttk.Radiobutton(
            transcription_frame, 
            text="OpenAI Whisper", 
            variable=self.transcription_service, 
            value="openai"
        ).pack(side=tk.LEFT)
        
        ttk.Radiobutton(
            transcription_frame, 
            text="ElevenLabs", 
            variable=self.transcription_service, 
            value="elevenlabs"
        ).pack(side=tk.LEFT, padx=(20, 0))
        
        # Idioma forzado
        ttk.Label(services_frame, text="Idioma forzado (opcional):").pack(anchor=tk.W, pady=(20, 5))
        self.forced_language = tk.StringVar(value=config.get('IDIOMA_FORZADO', ''))
        
        language_frame = ttk.Frame(services_frame)
        language_frame.pack(fill=tk.X, pady=5)
        
        language_combo = ttk.Combobox(
            language_frame, 
            textvariable=self.forced_language,
            values=['', 'es', 'en', 'fr', 'de', 'it', 'pt', 'ca'],
            state='readonly'
        )
        language_combo.pack(side=tk.LEFT)
        
        # Pestaña de procesamiento
        processing_frame = ttk.Frame(notebook)
        notebook.add(processing_frame, text="Procesamiento")
        
        # Límite de tamaño de archivo
        ttk.Label(processing_frame, text="Límite de archivo (MB):").pack(anchor=tk.W, pady=5)
        self.file_size_limit = tk.StringVar(value=str(config.get('FILE_SIZE_LIMIT_MB', '24')))
        ttk.Entry(processing_frame, textvariable=self.file_size_limit).pack(fill=tk.X, pady=5)
        
        # Duración de chunks
        ttk.Label(processing_frame, text="Duración de chunks (minutos):").pack(anchor=tk.W, pady=5)
        self.chunk_duration = tk.StringVar(value=str(config.get('CHUNK_DURATION_MIN', '10')))
        ttk.Entry(processing_frame, textvariable=self.chunk_duration).pack(fill=tk.X, pady=5)
        
        # Botones
        button_frame = ttk.Frame(self.root)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(
            button_frame, 
            text="Cancelar", 
            command=self.cancel
        ).pack(side=tk.RIGHT, padx=(10, 0))
        
        ttk.Button(
            button_frame, 
            text="Aceptar", 
            command=self.accept
        ).pack(side=tk.RIGHT)
    
    def accept(self):
        """Acepta la configuración"""
        self.result = {
            'TRANSCRIPTION_SERVICE': self.transcription_service.get(),
            'IDIOMA_FORZADO': self.forced_language.get(),
            'FILE_SIZE_LIMIT_MB': self.file_size_limit.get(),
            'CHUNK_DURATION_MIN': self.chunk_duration.get()
        }
        self.root.destroy()
    
    def cancel(self):
        """Cancela la configuración"""
        self.result = None
        self.root.destroy()
    
    def show(self) -> Optional[dict]:
        """Muestra el diálogo y retorna el resultado"""
        self.root.wait_window()
        return self.result


class MainApplication:
    """Aplicación principal con interfaz gráfica"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Audio2Text - Transcripción de Audio")
        self.root.geometry("600x400")
        
        # Variables
        self.processing = False
        self.current_config = {}
        
        self.setup_widgets()
        self.center_window()
    
    def setup_widgets(self):
        """Configura los widgets de la aplicación principal"""
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Título
        title_label = ttk.Label(
            main_frame, 
            text="Audio2Text",
            font=('Arial', 16, 'bold')
        )
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # Descripción
        desc_label = ttk.Label(
            main_frame,
            text="Convierte archivos de audio a texto usando IA",
            font=('Arial', 10)
        )
        desc_label.grid(row=1, column=0, columnspan=2, pady=(0, 30))
        
        # Botones principales
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, columnspan=2, pady=20)
        
        self.process_button = ttk.Button(
            button_frame,
            text="Procesar Archivo de Audio",
            command=self.start_processing,
            width=25
        )
        self.process_button.pack(pady=10)
        
        self.config_button = ttk.Button(
            button_frame,
            text="Configuración",
            command=self.show_configuration,
            width=25
        )
        self.config_button.pack(pady=5)
        
        self.exit_button = ttk.Button(
            button_frame,
            text="Salir",
            command=self.root.quit,
            width=25
        )
        self.exit_button.pack(pady=5)
        
        # Área de información
        info_frame = ttk.LabelFrame(main_frame, text="Información", padding="10")
        info_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=20)
        
        self.info_text = tk.Text(
            info_frame,
            height=8,
            width=60,
            wrap=tk.WORD,
            state=tk.DISABLED
        )
        
        scrollbar = ttk.Scrollbar(info_frame, orient=tk.VERTICAL, command=self.info_text.yview)
        self.info_text.configure(yscrollcommand=scrollbar.set)
        
        self.info_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Configurar grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        info_frame.columnconfigure(0, weight=1)
        
        # Mensaje inicial
        self.add_info_message("Bienvenido a Audio2Text. Seleccione 'Procesar Archivo de Audio' para comenzar.")
    
    def center_window(self):
        """Centra la ventana en la pantalla"""
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (600 // 2)
        y = (self.root.winfo_screenheight() // 2) - (400 // 2)
        self.root.geometry(f"+{x}+{y}")
    
    def add_info_message(self, message: str):
        """Añade un mensaje al área de información"""
        self.info_text.config(state=tk.NORMAL)
        self.info_text.insert(tk.END, f"{message}\n")
        self.info_text.see(tk.END)
        self.info_text.config(state=tk.DISABLED)
        self.root.update()
    
    def start_processing(self):
        """Inicia el procesamiento de audio (placeholder para conectar con el backend)"""
        if self.processing:
            messagebox.showwarning("Procesando", "Ya hay un procesamiento en curso.")
            return
        
        # Seleccionar archivo de audio
        audio_file = FileSelector.select_audio_file()
        if not audio_file:
            return
        
        # Seleccionar archivo de salida
        base_name = os.path.splitext(os.path.basename(audio_file))[0]
        output_file = FileSelector.select_output_file(f"{base_name}_transcript")
        if not output_file:
            return
        
        self.add_info_message(f"Archivo seleccionado: {audio_file}")
        self.add_info_message(f"Salida: {output_file}")
        
        # Aquí se conectaría con el procesador principal
        # Por ahora, solo mostramos un mensaje
        messagebox.showinfo(
            "Procesamiento",
            "Esta función se conectará con el procesador de audio.\n"
            f"Archivo: {audio_file}\n"
            f"Salida: {output_file}"
        )
    
    def show_configuration(self):
        """Muestra el diálogo de configuración"""
        dialog = ConfigurationDialog(self.root, self.current_config)
        result = dialog.show()
        
        if result:
            self.current_config.update(result)
            self.add_info_message("Configuración actualizada.")
    
    def run(self):
        """Ejecuta la aplicación"""
        self.root.mainloop()


class GUIManager:
    """Gestor principal de la interfaz gráfica"""
    
    def __init__(self, config_manager):
        self.config = config_manager
        
    def ask_force_language(self) -> Optional[str]:
        """Pregunta al usuario si quiere forzar el idioma"""
        root = tk.Tk()
        root.withdraw()
        
        response = messagebox.askyesno(
            "Forzar idioma", 
            "¿Deseas forzar el idioma a español?"
        )
        
        root.destroy()
        return "es" if response else None
    
    def get_user_files(self) -> tuple:
        """Obtiene los archivos de entrada y salida del usuario"""
        root = tk.Tk()
        root.withdraw()
        
        # Seleccionar archivo de audio
        input_file = FileSelector.select_audio_file()
        if not input_file:
            root.destroy()
            return None, None
        
        # Seleccionar archivo de salida
        base_name = os.path.splitext(os.path.basename(input_file))[0]
        output_file = FileSelector.select_output_file(f"{base_name}_transcript")
        
        root.destroy()
        
        if not output_file:
            return None, None
        
        return input_file, output_file
    
    def ask_continue_processing(self) -> bool:
        """Pregunta si el usuario quiere procesar otro archivo"""
        root = tk.Tk()
        root.withdraw()
        
        response = messagebox.askyesno(
            "Procesar otro audio",
            "¿Deseas procesar otro archivo de audio?"
        )
        
        root.destroy()
        return response
    
    def select_transcription_service(self) -> Optional[str]:
        """Permite al usuario seleccionar el servicio de transcripción"""
        print("Llamando a select_transcription_service...")
        try:
            current_service = self.config.get('TRANSCRIPTION_SERVICE', 'openai')
            print(f"Servicio actual: {current_service}")
            
            # Usar la función simple de selección que sabemos que funciona
            from simple_dialog import select_service
            print("Creando diálogo de selección...")
            selected_service = select_service(current_service)
            print(f"Diálogo cerrado, resultado: {selected_service}")
            
            return selected_service
            
        except Exception as e:
            logging.error(f"Error en selector de servicio: {e}")
            print(f"Error en selector de servicio: {e}")
            import traceback
            traceback.print_exc()
            # Fallback: usar el servicio actual si hay error
            return self.config.get('TRANSCRIPTION_SERVICE', 'openai')
    
    def show_error(self, title: str, message: str):
        """Muestra un mensaje de error"""
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(title, message)
        root.destroy()
    
    def show_info(self, title: str, message: str):
        """Muestra un mensaje de información"""
        root = tk.Tk()
        root.withdraw()
        messagebox.showinfo(title, message)
        root.destroy()