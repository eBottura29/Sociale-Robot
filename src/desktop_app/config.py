import sys
from pathlib import Path


SETTINGS_DIR = Path(__file__).resolve().parents[1] / "settings"
if str(SETTINGS_DIR) not in sys.path:
    sys.path.insert(0, str(SETTINGS_DIR))

from settings import load_settings


_SETTINGS = load_settings()
_DESKTOP = _SETTINGS.get("desktop_app", {})
_LLM = _DESKTOP.get("llm", {})
_SERIAL = _DESKTOP.get("serial", {})

EMOTIONS = list(
    _DESKTOP.get(
        "emotions",
        [
            "Happiness",
            "Fatigue",
            "Hunger",
            "Sadness",
            "Anxiety",
            "Affection",
            "Curiosity",
            "Frustration",
        ],
    )
)

LLM_MODEL_NAME = str(_LLM.get("model_name", "meta-llama/Llama-3.2-3B-Instruct"))
SENTIMENT_MODEL_NAME = str(_LLM.get("sentiment_model_name", "nlptown/bert-base-multilingual-uncased-sentiment"))
LLM_ALLOW_DOWNLOAD = bool(_LLM.get("allow_download", True))
LLM_MAX_NEW_TOKENS = int(_LLM.get("max_new_tokens", 22))
LLM_MIN_NEW_TOKENS = int(_LLM.get("min_new_tokens", 1))
LLM_REPETITION_PENALTY = float(_LLM.get("repetition_penalty", 1.08))
LLM_TEMPERATURE = float(_LLM.get("temperature", 0.7))
LLM_TOP_P = float(_LLM.get("top_p", 0.9))

SERIAL_BAUD = int(_SERIAL.get("baud", 9600))
SERIAL_TIMEOUT = float(_SERIAL.get("timeout", 0.1))

CONTROL_LAB_DEFAULTS = dict(_DESKTOP.get("control_lab", {}))
