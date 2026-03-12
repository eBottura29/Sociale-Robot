import importlib.util
import sys
from pathlib import Path


_BASE_DIR = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[2]))
_SETTINGS_MODULE = _BASE_DIR / "settings" / "settings.py"


def _load_settings_module():
    spec = importlib.util.spec_from_file_location("nier_settings", _SETTINGS_MODULE)
    if spec is None or spec.loader is None:
        raise ImportError("settings.py niet gevonden")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_SETTINGS = _load_settings_module()
load_settings = _SETTINGS.load_settings
save_settings = _SETTINGS.save_settings
