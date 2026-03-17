# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path
import os
import sys
from PyInstaller.utils.hooks import collect_submodules

tcl_root = Path(sys.base_prefix) / "tcl"
lib_root = Path(sys.base_prefix) / "Lib"
dll_root = Path(sys.base_prefix) / "DLLs"
datas = [
    ("src/settings/settings.json", "settings"),
    ("src/settings/settings.py", "settings"),
    ("src/desktop_app/tools/control_lab/keybinds.json", "."),
]
binaries = []

tk_pkg = lib_root / "tkinter"
if tk_pkg.exists():
    datas.append((str(tk_pkg), "tkinter"))

for dll_name in ("_tkinter.pyd", "tk86t.dll", "tcl86t.dll"):
    dll_path = dll_root / dll_name
    if dll_path.exists():
        binaries.append((str(dll_path), "."))
if tcl_root.exists():
    tcl_path = tcl_root / "tcl8.6"
    tk_path = tcl_root / "tk8.6"
    if tcl_path.exists():
        datas.append((str(tcl_path), "tcl/tcl8.6"))
        os.environ.setdefault("TCL_LIBRARY", str(tcl_path))
    if tk_path.exists():
        datas.append((str(tk_path), "tcl/tk8.6"))
        os.environ.setdefault("TK_LIBRARY", str(tk_path))

hiddenimports = [
    "config",
    "emotion_output_store",
    "eyebrow_store",
    "led_matrix_store",
    "serial_client",
    "settings_loader",
]
hiddenimports += collect_submodules("tkinter")

a = Analysis(
    ["src\\desktop_app\\tools\\control_lab\\control_lab_app.py"],
    pathex=[
        "src\\desktop_app\\tools\\control_lab",
        "src\\desktop_app\\firmware",
    ],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=["pyi_rth_tkinter.py"],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="control_app",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
