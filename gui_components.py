"""Interfaz grafica para la aplicacion Audio2Text."""

import logging
import os
import tkinter as tk
from pathlib import Path
from queue import Empty, Queue
from tkinter import filedialog, messagebox
from typing import Optional

import customtkinter as ctk


ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")


def _title_font(size: int = 16) -> ctk.CTkFont:
    """Devuelve una fuente de titulo consistente."""
    return ctk.CTkFont(size=size, weight="bold")


def _body_font(size: int = 12, weight: str = "normal") -> ctk.CTkFont:
    """Devuelve una fuente de cuerpo consistente."""
    return ctk.CTkFont(size=size, weight=weight)


def _center_window(window: tk.Misc, width: int, height: int) -> None:
    """Centra una ventana en la pantalla."""
    window.update_idletasks()
    x = (window.winfo_screenwidth() // 2) - (width // 2)
    y = (window.winfo_screenheight() // 2) - (height // 2)
    window.geometry(f"{width}x{height}+{x}+{y}")


def _bring_to_front(window: tk.Misc) -> None:
    """Trae una ventana al frente y fuerza el foco."""
    try:
        window.attributes("-topmost", True)
        window.lift()
        window.focus_force()
        window.after(
            100,
            lambda: window.attributes("-topmost", False)
            if window.winfo_exists()
            else None,
        )
    except tk.TclError:
        pass


def _safe_release_grab(window: tk.Misc) -> None:
    """Libera el grab modal si la ventana lo posee."""
    try:
        if window.grab_current() == window:
            window.grab_release()
    except tk.TclError:
        pass


def _get_dialog_parent() -> Optional[tk.Misc]:
    """Obtiene la raiz activa para dialogos del sistema."""
    root = getattr(tk, "_default_root", None)
    if root and root.winfo_exists():
        return root
    return None


def _create_hidden_root() -> tk.Tk:
    """Crea una raiz Tk oculta para dialogos del sistema."""
    root = ctk.CTk()
    root.withdraw()
    return root


def _destroy_window(window: Optional[tk.Misc]) -> None:
    """Destruye una ventana de forma segura."""
    if not window:
        return

    try:
        if not window.winfo_exists():
            return
        _safe_release_grab(window)
        window.withdraw()
        window.update_idletasks()
        window.destroy()
    except tk.TclError:
        pass


class ProgressDialog:
    """Dialogo de progreso para mostrar el estado del procesamiento."""

    def __init__(self, parent, title: str = "Procesando..."):
        self.parent = parent
        self.owns_root = parent is None
        self.cancelled = False
        self.closed = False
        self.progress_maximum = 1
        self.root = ctk.CTk() if self.owns_root else ctk.CTkToplevel(parent)
        self._ui_queue: Queue[tuple[str, object]] = Queue()
        self._ui_job = None
        self.root.title(title)
        self.root.resizable(False, False)
        _center_window(self.root, 420, 180)
        self.root.protocol("WM_DELETE_WINDOW", self.cancel)
        self.setup_widgets()

        if parent:
            self.root.transient(parent)
            self.root.grab_set()

        _bring_to_front(self.root)
        self._schedule_ui_processing()

    def setup_widgets(self):
        """Configura los widgets de la ventana de progreso."""
        main_frame = ctk.CTkFrame(self.root, corner_radius=16)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        self.status_label = ctk.CTkLabel(
            main_frame,
            text="Iniciando procesamiento...",
            font=_body_font(13),
            wraplength=340,
            justify="left",
        )
        self.status_label.pack(fill="x", padx=18, pady=(18, 14))

        self.progress_bar = ctk.CTkProgressBar(
            main_frame,
            width=340,
            mode="indeterminate",
        )
        self.progress_bar.pack(fill="x", padx=18, pady=(0, 16))
        self.progress_bar.start()

        self.cancel_button = ctk.CTkButton(
            main_frame,
            text="Cancelar",
            command=self.cancel,
            width=120,
        )
        self.cancel_button.pack(anchor="e", padx=18, pady=(0, 18))

    def update_status(self, message: str):
        """Actualiza el mensaje de estado."""
        self._ui_queue.put(("status", message))

    def set_determinate_progress(self, maximum: int):
        """Cambia la barra a progreso determinado."""
        self._ui_queue.put(("determinate", maximum))

    def update_progress(self, value: int):
        """Actualiza el valor del progreso."""
        self._ui_queue.put(("progress", value))

    def _schedule_ui_processing(self):
        """Programa el procesamiento de la cola de UI."""
        try:
            if self.closed or not self.root or not self.root.winfo_exists():
                return
            self._ui_job = self.root.after(100, self._process_ui_queue)
        except tk.TclError:
            self._ui_job = None

    def _process_ui_queue(self):
        """Procesa en el hilo principal las actualizaciones pendientes."""
        self._ui_job = None

        try:
            while True:
                action, value = self._ui_queue.get_nowait()

                if action == "status":
                    self.status_label.configure(text=str(value))
                elif action == "determinate":
                    self.progress_maximum = max(int(value), 1)
                    self.progress_bar.stop()
                    self.progress_bar.configure(mode="determinate")
                    self.progress_bar.set(0)
                elif action == "progress":
                    progress = max(
                        0.0,
                        min(float(value) / self.progress_maximum, 1.0),
                    )
                    self.progress_bar.set(progress)
        except Empty:
            pass
        except tk.TclError:
            pass
        finally:
            try:
                if self.root and self.root.winfo_exists():
                    self.root.update_idletasks()
            except tk.TclError:
                pass

            if not self.closed:
                self._schedule_ui_processing()

    def cancel(self):
        """Marca el dialogo como cancelado."""
        self.cancelled = True
        self.close()

    def close(self):
        """Cierra la ventana de progreso."""
        if self.closed:
            return

        self.closed = True

        try:
            if self._ui_job and self.root and self.root.winfo_exists():
                self.root.after_cancel(self._ui_job)
            if hasattr(self, "progress_bar"):
                self.progress_bar.stop()
            if hasattr(self, "root") and self.root:
                _destroy_window(self.root)
        except tk.TclError:
            pass
        except Exception:
            pass


class APIKeysDialog:
    """Dialogo para solicitar las claves API en el primer inicio."""

    def __init__(self, parent=None):
        self.parent = parent
        self.owns_root = parent is None
        self.result = None
        self.root = ctk.CTk() if self.owns_root else ctk.CTkToplevel(parent)
        self.root.title("Configuracion inicial de API Keys")
        self.root.resizable(False, False)
        _center_window(self.root, 560, 340)

        self.setup_widgets()

        self.root.protocol("WM_DELETE_WINDOW", self.cancel)
        self.root.bind("<Return>", lambda _event: self.accept())
        self.root.bind("<Escape>", lambda _event: self.cancel())

        if parent:
            self.root.transient(parent)
            self.root.grab_set()

        _bring_to_front(self.root)

    def setup_widgets(self):
        """Construye los widgets del dialogo."""
        main_frame = ctk.CTkFrame(self.root, corner_radius=18)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(
            main_frame,
            text="Bienvenido a Audio2Text",
            font=_title_font(18),
        ).pack(anchor="w", padx=20, pady=(20, 10))

        ctk.CTkLabel(
            main_frame,
            text=(
                "Para usar la aplicacion necesitas configurar al menos una "
                "clave API. Rellena una o ambas y presiona Guardar."
            ),
            font=_body_font(12),
            wraplength=480,
            justify="left",
        ).pack(anchor="w", fill="x", padx=20, pady=(0, 20))

        input_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        input_frame.pack(fill="x", padx=20)
        input_frame.grid_columnconfigure(1, weight=1)

        self.openai_var = tk.StringVar(master=self.root)
        self.elevenlabs_var = tk.StringVar(master=self.root)

        ctk.CTkLabel(
            input_frame,
            text="OpenAI API Key:",
            font=_body_font(12, "bold"),
        ).grid(row=0, column=0, sticky="w", pady=(0, 12))
        self.openai_entry = ctk.CTkEntry(
            input_frame,
            textvariable=self.openai_var,
            show="*",
            width=360,
        )
        self.openai_entry.grid(row=0, column=1, sticky="ew", padx=(16, 0), pady=(0, 12))

        ctk.CTkLabel(
            input_frame,
            text="ElevenLabs API Key:",
            font=_body_font(12, "bold"),
        ).grid(row=1, column=0, sticky="w")
        self.elevenlabs_entry = ctk.CTkEntry(
            input_frame,
            textvariable=self.elevenlabs_var,
            show="*",
            width=360,
        )
        self.elevenlabs_entry.grid(row=1, column=1, sticky="ew", padx=(16, 0))

        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill="x", padx=20, pady=(24, 20))

        self.btn_cancel = ctk.CTkButton(
            button_frame,
            text="Salir",
            command=self.cancel,
            width=120,
            fg_color=("gray70", "gray28"),
            hover_color=("gray60", "gray35"),
        )
        self.btn_cancel.pack(side="right")

        self.btn_save = ctk.CTkButton(
            button_frame,
            text="Guardar y continuar",
            command=self.accept,
            width=170,
        )
        self.btn_save.pack(side="right", padx=(0, 10))

        self.openai_entry.focus_set()

    def accept(self):
        """Guarda las claves si la entrada es valida."""
        openai_key = self.openai_var.get().strip()
        elevenlabs_key = self.elevenlabs_var.get().strip()

        if not openai_key and not elevenlabs_key:
            messagebox.showwarning(
                "Faltan claves",
                "Debes ingresar al menos una clave API para continuar.",
                parent=self.root,
            )
            return

        self.result = {
            "OPENAI_API_KEY": openai_key,
            "ELEVENLABS_API_KEY": elevenlabs_key,
        }
        self.cancelled = False
        self._close()

    def cancel(self):
        """Cancela el dialogo."""
        self.result = None
        self._close()

    def _close(self):
        """Cierra el dialogo de forma segura."""
        _destroy_window(self.root)

    def show(self) -> Optional[dict]:
        """Muestra el dialogo y devuelve el resultado."""
        if self.owns_root:
            self.root.mainloop()
        else:
            self.root.wait_window()
        return self.result


class FileSelector:
    """Manejador para seleccion de archivos."""

    ALLOWED_OUTPUT_EXTENSIONS = {".txt", ".md"}

    @staticmethod
    def select_audio_file() -> Optional[str]:
        """Permite al usuario seleccionar un archivo de audio."""
        parent = _get_dialog_parent()
        file_types = [
            ("Archivos de audio", "*.mp3 *.wav *.m4a *.aac *.ogg *.flac"),
            ("MP3 files", "*.mp3"),
            ("WAV files", "*.wav"),
            ("M4A files", "*.m4a"),
            ("Todos los archivos", "*.*"),
        ]

        file_path = filedialog.askopenfilename(
            title="Seleccione el archivo de audio",
            filetypes=file_types,
            parent=parent,
        )

        return file_path if file_path else None

    @staticmethod
    def select_output_file(default_name: str = "transcription") -> Optional[str]:
        """Permite al usuario seleccionar donde guardar el archivo de salida."""
        parent = _get_dialog_parent()
        file_path = filedialog.asksaveasfilename(
            title="Seleccione donde guardar la transcripcion",
            defaultextension=".txt",
            initialfile=f"{default_name}.txt",
            filetypes=[
                ("Archivos de texto", "*.txt"),
                ("Archivos Markdown", "*.md"),
            ],
            parent=parent,
        )

        if not file_path:
            return None

        output_path = Path(file_path)
        if not output_path.suffix:
            output_path = output_path.with_suffix(".txt")
        elif output_path.suffix.lower() not in FileSelector.ALLOWED_OUTPUT_EXTENSIONS:
            messagebox.showerror(
                "Extension no permitida",
                "Solo se permite guardar la transcripcion como .txt o .md.",
                parent=parent,
            )
            return None

        return str(output_path)


class ServiceSelectionDialog:
    """Dialogo para seleccionar el servicio de transcripcion."""

    def __init__(self, parent, current_service: str = "local"):
        self.parent = parent
        self.owns_root = parent is None
        self.result = None
        self.root = ctk.CTk() if self.owns_root else ctk.CTkToplevel(parent)
        self.root.title("Seleccionar servicio de transcripcion")
        self.root.resizable(True, False)
        self.root.minsize(700, 620)
        self.selected_service = tk.StringVar(
            master=self.root,
            value=current_service,
        )

        self.center_window()
        self.setup_widgets(current_service)

        self.root.protocol("WM_DELETE_WINDOW", self.cancel)
        self.root.bind("<Return>", lambda _event: self.accept())
        self.root.bind("<Escape>", lambda _event: self.cancel())

        if parent:
            self.root.transient(parent)
            self.root.grab_set()

        _bring_to_front(self.root)

    def center_window(self):
        """Centra la ventana en la pantalla."""
        _center_window(self.root, 700, 620)

    def setup_widgets(self, current_service: str):
        """Configura los widgets del dialogo."""
        self.selected_service.set(current_service)

        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(0, weight=1)

        main_frame = ctk.CTkFrame(self.root, corner_radius=18)
        main_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(2, weight=1)

        ctk.CTkLabel(
            main_frame,
            text="Seleccionar servicio de transcripcion",
            font=_title_font(18),
        ).grid(row=0, column=0, sticky="w", padx=20, pady=(20, 18))

        options_frame = ctk.CTkFrame(main_frame)
        options_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 16))

        ctk.CTkLabel(
            options_frame,
            text="Servicios disponibles",
            font=_body_font(13, "bold"),
        ).pack(anchor="w", padx=16, pady=(16, 6))

        openai_frame = ctk.CTkFrame(options_frame, fg_color="transparent")
        openai_frame.pack(fill="x", padx=16, pady=8)
        self.openai_radio = ctk.CTkRadioButton(
            openai_frame,
            text="OpenAI Whisper",
            variable=self.selected_service,
            value="openai",
        )
        self.openai_radio.pack(side="left")
        ctk.CTkLabel(
            openai_frame,
            text="Muy preciso, soporta multiples idiomas",
            font=_body_font(11),
            text_color=("gray35", "gray70"),
            justify="left",
            wraplength=420,
        ).pack(side="left", padx=(12, 0))

        elevenlabs_frame = ctk.CTkFrame(options_frame, fg_color="transparent")
        elevenlabs_frame.pack(fill="x", padx=16, pady=(0, 10))
        self.elevenlabs_radio = ctk.CTkRadioButton(
            elevenlabs_frame,
            text="ElevenLabs",
            variable=self.selected_service,
            value="elevenlabs",
        )
        self.elevenlabs_radio.pack(side="left")
        ctk.CTkLabel(
            elevenlabs_frame,
            text="Rapido, alta calidad de transcripcion",
            font=_body_font(11),
            text_color=("gray35", "gray70"),
            justify="left",
            wraplength=420,
        ).pack(side="left", padx=(12, 0))

        local_frame = ctk.CTkFrame(options_frame, fg_color="transparent")
        local_frame.pack(fill="x", padx=16, pady=(0, 16))
        self.local_radio = ctk.CTkRadioButton(
            local_frame,
            text="Modelo local (Faster-Whisper)",
            variable=self.selected_service,
            value="local",
        )
        self.local_radio.pack(side="left")
        ctk.CTkLabel(
            local_frame,
            text=(
                "No requiere API Key. Descarga el modelo en el primer uso "
                "y consume CPU/RAM."
            ),
            font=_body_font(11),
            text_color=("gray35", "gray70"),
            justify="left",
            wraplength=420,
        ).pack(side="left", padx=(12, 0))

        info_frame = ctk.CTkFrame(main_frame)
        info_frame.grid(row=2, column=0, sticky="nsew", padx=20, pady=(0, 18))
        ctk.CTkLabel(
            info_frame,
            text="Informacion",
            font=_body_font(13, "bold"),
        ).pack(anchor="w", padx=16, pady=(16, 6))
        ctk.CTkLabel(
            info_frame,
            text=(
                "- OpenAI Whisper: excelente precision y muchos idiomas\n"
                "- ElevenLabs: procesamiento rapido y buena calidad\n"
                "- Modelo local (Faster-Whisper): sin API key, descarga inicial y mayor uso de recursos\n"
                "- OpenAI y ElevenLabs requieren claves API validas"
            ),
            font=_body_font(12),
            justify="left",
            wraplength=600,
        ).pack(anchor="w", padx=16, pady=(0, 16))

        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.grid(row=3, column=0, sticky="ew", padx=20, pady=(0, 20))
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=0)
        button_frame.grid_columnconfigure(2, weight=0)

        helper_label = ctk.CTkLabel(
            button_frame,
            text="Pulsa Siguiente para elegir el archivo de audio.",
            font=_body_font(11),
            text_color=("gray35", "gray70"),
            justify="left",
            anchor="w",
        )
        helper_label.grid(row=0, column=0, columnspan=3, sticky="ew", pady=(0, 10))

        self.cancel_button = ctk.CTkButton(
            button_frame,
            text="Cancelar",
            command=self.cancel,
            width=120,
            fg_color=("gray70", "gray28"),
            hover_color=("gray60", "gray35"),
        )
        self.cancel_button.grid(row=1, column=2, sticky="e")

        self.accept_button = ctk.CTkButton(
            button_frame,
            text="Siguiente",
            command=self.accept,
            width=130,
        )
        self.accept_button.grid(row=1, column=1, sticky="e", padx=(0, 10))
        self.accept_button.focus_set()

    def accept(self):
        """Acepta la seleccion."""
        try:
            self.result = self.selected_service.get()
            logging.info("Usuario selecciono servicio: %s", self.result)
            self.close_dialog()
        except Exception as exc:
            logging.error("Error al aceptar seleccion: %s", exc)
            self.result = "local"
            self.close_dialog()

    def cancel(self):
        """Cancela la seleccion."""
        logging.info("Usuario cancelo seleccion de servicio")
        self.result = None
        self.close_dialog()

    def close_dialog(self):
        """Cierra el dialogo de manera segura."""
        try:
            _destroy_window(self.root)
        except Exception as exc:
            logging.error("Error cerrando dialogo: %s", exc)

    def show(self) -> Optional[str]:
        """Muestra el dialogo y retorna el servicio seleccionado."""
        try:
            if self.owns_root:
                self.root.mainloop()
            else:
                self.root.wait_window()
            return self.result
        except Exception as exc:
            logging.error("Error mostrando dialogo: %s", exc)
            return None


class ConfigurationDialog:
    """Dialogo para configuracion de opciones."""

    def __init__(self, parent, current_config: dict):
        self.parent = parent
        self.owns_root = parent is None
        self.result = None
        self.root = ctk.CTk() if self.owns_root else ctk.CTkToplevel(parent)
        self.root.title("Configuracion")
        self.root.resizable(True, True)
        _center_window(self.root, 560, 460)
        self.root.protocol("WM_DELETE_WINDOW", self.cancel)

        self.setup_widgets(current_config)

        if parent:
            self.root.transient(parent)
            self.root.grab_set()

        _bring_to_front(self.root)

    def setup_widgets(self, config: dict):
        """Configura los widgets del dialogo de configuracion."""
        main_frame = ctk.CTkFrame(self.root, corner_radius=18)
        main_frame.pack(fill="both", expand=True, padx=16, pady=16)

        self.tabview = ctk.CTkTabview(main_frame)
        self.tabview.pack(fill="both", expand=True, padx=16, pady=(16, 12))

        self.tabview.add("Servicios")
        self.tabview.add("Procesamiento")
        self.tabview.set("Servicios")

        services_frame = self.tabview.tab("Servicios")
        processing_frame = self.tabview.tab("Procesamiento")

        self.transcription_service = tk.StringVar(
            master=self.root,
            value=config.get("TRANSCRIPTION_SERVICE", "local")
        )
        self.forced_language = tk.StringVar(
            master=self.root,
            value=config.get("IDIOMA_FORZADO", "")
        )
        self.file_size_limit = tk.StringVar(
            master=self.root,
            value=str(config.get("FILE_SIZE_LIMIT_MB", "24"))
        )
        self.chunk_duration = tk.StringVar(
            master=self.root,
            value=str(config.get("CHUNK_DURATION_MIN", "10"))
        )

        ctk.CTkLabel(
            services_frame,
            text="Servicio de transcripcion:",
            font=_body_font(12, "bold"),
        ).pack(anchor="w", padx=12, pady=(14, 8))

        transcription_frame = ctk.CTkFrame(services_frame, fg_color="transparent")
        transcription_frame.pack(fill="x", padx=12, pady=(0, 16))

        ctk.CTkRadioButton(
            transcription_frame,
            text="OpenAI Whisper",
            variable=self.transcription_service,
            value="openai",
        ).pack(anchor="w", pady=(0, 6))

        ctk.CTkRadioButton(
            transcription_frame,
            text="ElevenLabs",
            variable=self.transcription_service,
            value="elevenlabs",
        ).pack(anchor="w", pady=(0, 6))

        ctk.CTkRadioButton(
            transcription_frame,
            text="Modelo local (Faster-Whisper)",
            variable=self.transcription_service,
            value="local",
        ).pack(anchor="w")

        ctk.CTkLabel(
            services_frame,
            text="Idioma forzado (opcional):",
            font=_body_font(12, "bold"),
        ).pack(anchor="w", padx=12, pady=(0, 8))

        self.language_combo = ctk.CTkComboBox(
            services_frame,
            variable=self.forced_language,
            values=["", "es", "en", "fr", "de", "it", "pt", "ca"],
            state="readonly",
            width=180,
        )
        self.language_combo.pack(anchor="w", padx=12, pady=(0, 14))

        ctk.CTkLabel(
            processing_frame,
            text="Limite de archivo (MB):",
            font=_body_font(12, "bold"),
        ).pack(anchor="w", padx=12, pady=(14, 8))

        ctk.CTkEntry(
            processing_frame,
            textvariable=self.file_size_limit,
            width=180,
        ).pack(anchor="w", padx=12, pady=(0, 16))

        ctk.CTkLabel(
            processing_frame,
            text="Duracion de chunks (minutos):",
            font=_body_font(12, "bold"),
        ).pack(anchor="w", padx=12, pady=(0, 8))

        ctk.CTkEntry(
            processing_frame,
            textvariable=self.chunk_duration,
            width=180,
        ).pack(anchor="w", padx=12, pady=(0, 14))

        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill="x", padx=16, pady=(0, 16))

        ctk.CTkButton(
            button_frame,
            text="Cancelar",
            command=self.cancel,
            width=120,
            fg_color=("gray70", "gray28"),
            hover_color=("gray60", "gray35"),
        ).pack(side="right")

        ctk.CTkButton(
            button_frame,
            text="Aceptar",
            command=self.accept,
            width=120,
        ).pack(side="right", padx=(0, 10))

    def accept(self):
        """Acepta la configuracion."""
        self.result = {
            "TRANSCRIPTION_SERVICE": self.transcription_service.get(),
            "IDIOMA_FORZADO": self.forced_language.get(),
            "FILE_SIZE_LIMIT_MB": self.file_size_limit.get(),
            "CHUNK_DURATION_MIN": self.chunk_duration.get(),
        }
        self._close()

    def cancel(self):
        """Cancela la configuracion."""
        self.result = None
        self._close()

    def _close(self):
        """Cierra el dialogo."""
        _destroy_window(self.root)

    def show(self) -> Optional[dict]:
        """Muestra el dialogo y retorna el resultado."""
        if self.owns_root:
            self.root.mainloop()
        else:
            self.root.wait_window()
        return self.result


class MainApplication:
    """Aplicacion principal con interfaz grafica."""

    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("Audio2Text - Transcripcion de Audio")
        self.root.resizable(True, True)

        self.processing = False
        self.current_config = {}

        self.setup_widgets()
        self.center_window()

    def setup_widgets(self):
        """Configura los widgets de la aplicacion principal."""
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(0, weight=1)

        main_frame = ctk.CTkFrame(self.root, corner_radius=18)
        main_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(3, weight=1)

        ctk.CTkLabel(
            main_frame,
            text="Audio2Text",
            font=_title_font(24),
        ).grid(row=0, column=0, pady=(24, 10), padx=24, sticky="n")

        ctk.CTkLabel(
            main_frame,
            text="Convierte archivos de audio a texto usando IA",
            font=_body_font(13),
        ).grid(row=1, column=0, pady=(0, 24), padx=24, sticky="n")

        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.grid(row=2, column=0, pady=(0, 20), padx=24, sticky="n")

        self.process_button = ctk.CTkButton(
            button_frame,
            text="Procesar archivo de audio",
            command=self.start_processing,
            width=280,
            height=40,
        )
        self.process_button.pack(pady=8)

        self.config_button = ctk.CTkButton(
            button_frame,
            text="Configuracion",
            command=self.show_configuration,
            width=280,
            height=40,
        )
        self.config_button.pack(pady=8)

        self.exit_button = ctk.CTkButton(
            button_frame,
            text="Salir",
            command=self.root.quit,
            width=280,
            height=40,
            fg_color=("gray70", "gray28"),
            hover_color=("gray60", "gray35"),
        )
        self.exit_button.pack(pady=8)

        info_frame = ctk.CTkFrame(main_frame)
        info_frame.grid(row=3, column=0, sticky="nsew", padx=24, pady=(0, 24))
        info_frame.grid_columnconfigure(0, weight=1)
        info_frame.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            info_frame,
            text="Informacion",
            font=_body_font(13, "bold"),
        ).grid(row=0, column=0, sticky="w", padx=18, pady=(16, 8))

        self.info_text = ctk.CTkTextbox(
            info_frame,
            wrap="word",
            height=190,
            font=_body_font(12),
        )
        self.info_text.grid(row=1, column=0, sticky="nsew", padx=18, pady=(0, 18))
        self.info_text.configure(state="disabled")

        self.add_info_message(
            "Bienvenido a Audio2Text. Seleccione 'Procesar archivo de audio' "
            "para comenzar."
        )

    def center_window(self):
        """Centra la ventana en la pantalla."""
        _center_window(self.root, 680, 520)

    def add_info_message(self, message: str):
        """Anade un mensaje al area de informacion."""
        self.info_text.configure(state="normal")
        self.info_text.insert("end", f"{message}\n")
        self.info_text.see("end")
        self.info_text.configure(state="disabled")
        self.root.update_idletasks()

    def start_processing(self):
        """Inicia el procesamiento de audio."""
        if self.processing:
            messagebox.showwarning(
                "Procesando",
                "Ya hay un procesamiento en curso.",
                parent=self.root,
            )
            return

        audio_file = FileSelector.select_audio_file()
        if not audio_file:
            return

        base_name = os.path.splitext(os.path.basename(audio_file))[0]
        output_file = FileSelector.select_output_file(f"{base_name}_transcript")
        if not output_file:
            return

        self.add_info_message(f"Archivo seleccionado: {audio_file}")
        self.add_info_message(f"Salida: {output_file}")

        messagebox.showinfo(
            "Procesamiento",
            "Esta funcion se conectara con el procesador de audio.\n"
            f"Archivo: {audio_file}\n"
            f"Salida: {output_file}",
            parent=self.root,
        )

    def show_configuration(self):
        """Muestra el dialogo de configuracion."""
        dialog = ConfigurationDialog(self.root, self.current_config)
        result = dialog.show()

        if result:
            self.current_config.update(result)
            self.add_info_message("Configuracion actualizada.")

    def run(self):
        """Ejecuta la aplicacion."""
        self.root.mainloop()


class GUIManager:
    """Gestor principal de la interfaz grafica."""

    def __init__(self, config_manager):
        self.config = config_manager
        self._root: Optional[tk.Misc] = None

    def get_root(self) -> tk.Misc:
        """Devuelve una raiz CTk oculta y persistente."""
        if self._root and self._root.winfo_exists():
            return self._root

        self._root = _create_hidden_root()
        return self._root

    def ask_force_language(self) -> Optional[str]:
        """Ya no preguntamos al usuario si quiere forzar el idioma."""
        return None

    def get_user_files(self) -> tuple:
        """Obtiene los archivos de entrada y salida del usuario."""
        self.get_root()

        input_file = FileSelector.select_audio_file()
        if not input_file:
            return None, None

        base_name = os.path.splitext(os.path.basename(input_file))[0]
        output_file = FileSelector.select_output_file(f"{base_name}_transcript")
        if not output_file:
            return None, None

        return input_file, output_file

    def ask_continue_processing(self) -> bool:
        """Pregunta si el usuario quiere procesar otro archivo."""
        return messagebox.askyesno(
            "Procesar otro audio",
            "Deseas procesar otro archivo de audio?",
            parent=self.get_root(),
        )

    def select_transcription_service(self) -> Optional[str]:
        """Permite al usuario seleccionar el servicio de transcripcion."""
        current_service = self.config.get("TRANSCRIPTION_SERVICE", "local")
        try:
            dialog = ServiceSelectionDialog(self.get_root(), current_service)
            return dialog.show()
        except Exception as exc:
            logging.error("Error en selector de servicio: %s", exc)
            return self.config.get("TRANSCRIPTION_SERVICE", "local")

    def show_error(self, title: str, message: str):
        """Muestra un mensaje de error."""
        messagebox.showerror(title, message, parent=self.get_root())

    def show_info(self, title: str, message: str):
        """Muestra un mensaje de informacion."""
        messagebox.showinfo(title, message, parent=self.get_root())
