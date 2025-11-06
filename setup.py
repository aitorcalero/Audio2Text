from cx_Freeze import setup, Executable

setup(
    name="Audio2Text",
    version="0.1",
    description="Convierte archivos de audio en textos resumidos",
    executables=[Executable("audio2text_gui.py")],
)