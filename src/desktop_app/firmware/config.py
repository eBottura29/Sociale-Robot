from settings_loader import load_settings


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
_fallback_models_raw = _LLM.get(
    "fallback_model_names",
    [
        "Qwen/Qwen2.5-0.5B-Instruct",
        "TinyLlama/TinyLlama-1.1B-Chat-v1.0",
    ],
)
if isinstance(_fallback_models_raw, str):
    LLM_FALLBACK_MODEL_NAMES = [
        name.strip() for name in _fallback_models_raw.split(",") if name.strip()
    ]
elif isinstance(_fallback_models_raw, list):
    LLM_FALLBACK_MODEL_NAMES = [
        str(name).strip() for name in _fallback_models_raw if str(name).strip()
    ]
else:
    LLM_FALLBACK_MODEL_NAMES = []
SENTIMENT_MODEL_NAME = str(_LLM.get("sentiment_model_name", "nlptown/bert-base-multilingual-uncased-sentiment"))
LLM_ALLOW_DOWNLOAD = bool(_LLM.get("allow_download", True))
LLM_MAX_NEW_TOKENS = int(_LLM.get("max_new_tokens", 22))
LLM_MIN_NEW_TOKENS = int(_LLM.get("min_new_tokens", 1))
LLM_REPETITION_PENALTY = float(_LLM.get("repetition_penalty", 1.08))
LLM_TEMPERATURE = float(_LLM.get("temperature", 0.7))
LLM_TOP_P = float(_LLM.get("top_p", 0.9))

SERIAL_BAUD = int(_SERIAL.get("baud", 9600))
SERIAL_TIMEOUT = float(_SERIAL.get("timeout", 0.1))
PAN_AUTO_SPEED_MS = int(_DESKTOP.get("pan_auto_speed_ms", 120))
EMOTION_BUZZER_ENABLED = bool(_DESKTOP.get("emotion_buzzer_enabled", True))
EMOTION_BUZZER_MIN_INTENSITY = int(_DESKTOP.get("emotion_buzzer_min_intensity", 35))

CONTROL_LAB_DEFAULTS = dict(_DESKTOP.get("control_lab", {}))
