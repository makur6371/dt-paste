# -*- mode: python ; coding: utf-8 -*-
import os
import sys
from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# 收集 paddleocr / pystray / pynput 等的隐藏导入与数据文件
paddle_datas = []
try:
    paddle_datas += collect_data_files("paddleocr")
    paddle_datas += collect_data_files("paddle")
except Exception:
    pass

hidden = [
    "PIL._tkinter_finder",
    "pystray._win32",
]
for mod in ["paddleocr", "pynput", "pystray", "pytesseract"]:
    try:
        hidden += collect_submodules(mod)
    except Exception:
        pass

a = Analysis(
    ["src/main.py"],
    pathex=[],
    binaries=[],
    datas=paddle_datas,
    hiddenimports=hidden,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["matplotlib", "pandas", "scipy"],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="ClipOCR",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,                    # TEMP: enable console to surface startup errors
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
