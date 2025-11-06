"""
Diálogo simple y funcional para selección de servicio
"""
import tkinter as tk
from tkinter import ttk
from typing import Optional


def select_service(current_service: str = "openai") -> Optional[str]:
    """
    Función simple para seleccionar el servicio de transcripción
    Basada en el diálogo de prueba que funciona correctamente
    """
    print("=== SELECCIÓN DE SERVICIO ===")
    
    result = None
    
    # Crear ventana principal
    root = tk.Tk()
    root.title("Seleccionar Servicio de Transcripción")
    root.geometry("400x300")
    root.resizable(False, False)
    
    # Centrar ventana
    root.update_idletasks()
    width = 400
    height = 300
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f"{width}x{height}+{x}+{y}")
    
    # Frame principal
    main_frame = ttk.Frame(root, padding="20")
    main_frame.pack(fill=tk.BOTH, expand=True)
    
    # Título
    title_label = ttk.Label(
        main_frame, 
        text="Selecciona el Servicio de Transcripción",
        font=("Arial", 12, "bold")
    )
    title_label.pack(pady=(0, 20))
    
    # Variable para la selección
    selected_service = tk.StringVar(value=current_service)
    
    # Opciones de servicio
    services = [
        ("openai", "OpenAI Whisper\n(Requiere API key de OpenAI)"),
        ("elevenlabs", "ElevenLabs Speech-to-Text\n(Requiere API key de ElevenLabs)")
    ]
    
    for service_id, description in services:
        frame = ttk.Frame(main_frame)
        frame.pack(fill=tk.X, pady=5)
        
        radio = ttk.Radiobutton(
            frame,
            text=description,
            variable=selected_service,
            value=service_id
        )
        radio.pack(anchor=tk.W)
    
    # Frame para botones
    button_frame = ttk.Frame(main_frame)
    button_frame.pack(fill=tk.X, pady=(20, 0))
    
    # Funciones para botones
    def accept():
        nonlocal result
        result = selected_service.get()
        print(f"Usuario seleccionó: {result}")
        root.quit()
        root.destroy()
    
    def cancel():
        nonlocal result
        result = None
        print("Usuario canceló la selección")
        root.quit()
        root.destroy()
    
    # Botones
    ttk.Button(button_frame, text="Cancelar", command=cancel).pack(side=tk.LEFT)
    ttk.Button(button_frame, text="Aceptar", command=accept).pack(side=tk.RIGHT)
    
    # Configurar eventos
    root.protocol("WM_DELETE_WINDOW", cancel)
    root.bind('<Return>', lambda e: accept())
    root.bind('<Escape>', lambda e: cancel())
    
    # Forzar que la ventana aparezca
    root.attributes('-topmost', True)
    root.lift()
    root.focus_force()
    root.after(100, lambda: root.attributes('-topmost', False))
    
    print("Ventana creada, ejecutando mainloop...")
    print("NOTA: Si no ves la ventana, revisa la barra de tareas de Windows")
    
    # Ejecutar
    root.mainloop()
    
    print("Ventana destruida correctamente")
    return result


if __name__ == "__main__":
    # Prueba del diálogo
    service = select_service("openai")
    print(f"Resultado final: {service}")