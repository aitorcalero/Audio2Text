# -*- mode: python ; coding: utf-8 -*-
import sys
from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files

block_cipher = None

# Usar cwd porque __file__ no está definido al ejecutar el spec
here = Path.cwd()

# Datos adicionales: perfiles de langdetect y la plantilla de config
datas = collect_data_files("langdetect")
datas.append((str(here / "config.example.json"), "."))

# Binarios adicionales: ffmpeg opcional si está junto al proyecto
binaries = []
ffmpeg_path = here / "ffmpeg.exe"
if ffmpeg_path.exists():
    binaries.append((str(ffmpeg_path), "."))

a = Analysis(
    ["main.py"],
    pathex=[str(here)],
    binaries=binaries,
    datas=datas,
    hiddenimports=["langdetect.lang_detect_exception"],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Audio2Text",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="Audio2Text",
)
