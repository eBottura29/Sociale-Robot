import os
import sys
from pathlib import Path

# Ensure Tcl/Tk is discoverable at runtime inside a PyInstaller bundle.
base = Path(getattr(sys, '_MEIPASS', Path.cwd()))
tcl_dir = base / 'tcl' / 'tcl8.6'
tk_dir = base / 'tcl' / 'tk8.6'
if tcl_dir.exists():
    os.environ.setdefault('TCL_LIBRARY', str(tcl_dir))
if tk_dir.exists():
    os.environ.setdefault('TK_LIBRARY', str(tk_dir))
