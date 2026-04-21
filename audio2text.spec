# -*- mode: python ; coding: utf-8 -*-
import os
import sys
from pathlib import Path
from PyInstaller.utils.hooks import (
    collect_data_files,
    collect_dynamic_libs,
    collect_submodules,
)

block_cipher = None

# Usar cwd porque __file__ no está definido al ejecutar el spec
here = Path.cwd()

# Datos adicionales: perfiles de langdetect, assets de customtkinter
# y la plantilla de config
datas = collect_data_files("langdetect")
datas += collect_data_files("customtkinter")
datas += collect_data_files("faster_whisper")
datas.append((str(here / "config.example.json"), "."))

# Binarios adicionales: ffmpeg solo si se solicita explícitamente
binaries = collect_dynamic_libs("ctranslate2")
binaries += collect_dynamic_libs("av")

hiddenimports = ["langdetect.lang_detect_exception"]
hiddenimports += collect_submodules("faster_whisper")
hiddenimports += collect_submodules("ctranslate2")
hiddenimports += collect_submodules("av")

bundle_ffmpeg = os.environ.get("AUDIO2TEXT_BUNDLE_FFMPEG", "").lower() in {"1", "true", "yes", "on"}
ffmpeg_override = os.environ.get("AUDIO2TEXT_FFMPEG_PATH")

if bundle_ffmpeg:
    ffmpeg_path = Path(ffmpeg_override) if ffmpeg_override else here / "ffmpeg.exe"
    if ffmpeg_path.name.lower() != "ffmpeg.exe":
        raise SystemExit("AUDIO2TEXT_FFMPEG_PATH debe apuntar a un archivo llamado ffmpeg.exe")
    if not ffmpeg_path.exists():
        raise SystemExit("AUDIO2TEXT_BUNDLE_FFMPEG está activo pero no se encontró ffmpeg.exe")
    binaries.append((str(ffmpeg_path.resolve()), "."))

a = Analysis(
    ["main.py"],
    pathex=[str(here)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
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
