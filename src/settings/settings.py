import copy
import json
from pathlib import Path
from typing import Any


SETTINGS_PATH = Path(__file__).with_name("settings.json")


def _merge_dict(base: dict, override: dict) -> dict:
    merged = copy.deepcopy(base)
    for key, value in override.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = _merge_dict(merged[key], value)
        else:
            merged[key] = value
    return merged


def default_settings() -> dict:
    return {
        "desktop_app": {
            "emotions": [
                "Happiness",
                "Fatigue",
                "Hunger",
                "Sadness",
                "Anxiety",
                "Affection",
                "Curiosity",
                "Frustration",
            ],
            "serial": {
                "baud": 9600,
                "timeout": 0.1,
            },
            "llm": {
                "model_name": "meta-llama/Llama-3.2-3B-Instruct",
                "sentiment_model_name": "nlptown/bert-base-multilingual-uncased-sentiment",
                "allow_download": True,
                "max_new_tokens": 22,
                "min_new_tokens": 1,
                "repetition_penalty": 1.08,
                "temperature": 0.7,
                "top_p": 0.9,
            },
            "control_lab": {
                "window_width": 1220,
                "window_height": 840,
                "window_min_width": 1080,
                "window_min_height": 760,
                "default_drive_speed": 80,
                "default_emotion_intensity": 70,
                "default_pan_angle": 90,
                "default_brow_left": 90,
                "default_brow_right": 90,
                "default_rgb_r": 0,
                "default_rgb_g": 0,
                "default_rgb_b": 0,
                "default_buzzer_pitch": 880,
            },
        },
        "robot": {
            "pins": {
                "drive_left": 41,
                "drive_right": 40,
                "sonar_pan": 19,
                "eyebrow_left": 18,
                "eyebrow_right": 17,
                "echo_left": "A0",
                "echo_right": "A2",
                "trigger_left": "A1",
                "trigger_right": "A3",
            },
            "limits": {
                "max_distance_cm": 200,
                "max_velocity": 50,
                "buzzer_min_pitch": 100,
                "buzzer_max_pitch": 5000,
            },
            "timing": {
                "telemetry_interval_ms": 250,
                "command_timeout_ms": 1000,
                "lcd_scroll_interval_ms": 450,
                "sonar_scan_settle_ms": 140,
                "sonar_pan_step_interval_ms": 20,
            },
            "navigation": {
                "sonar_pan_step_deg": 2,
                "avoid_threshold_cm": 20,
                "approach_threshold_cm": 60,
                "avoid_speed": 40,
                "approach_slow_speed": 25,
                "approach_fast_speed": 45,
                "search_forward_speed": 35,
                "search_turn_speed": 30,
                "search_forward_ms": 1200,
                "search_turn_ms": 800,
            },
            "defaults": {
                "sonar_scan_angles": [20, 90, 160],
                "eyebrow_angles_by_emotion": {
                    "HAPPINESS": [120, 60],
                    "FATIGUE": [75, 105],
                    "HUNGER": [85, 95],
                    "SADNESS": [65, 115],
                    "ANXIETY": [140, 40],
                    "AFFECTION": [110, 70],
                    "CURIOSITY": [130, 50],
                    "FRUSTRATION": [45, 135],
                },
            },
        },
    }


def load_settings() -> dict:
    defaults = default_settings()
    if not SETTINGS_PATH.exists():
        save_settings(defaults)
        return defaults
    try:
        user = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
        if not isinstance(user, dict):
            return defaults
        return _merge_dict(defaults, user)
    except (OSError, json.JSONDecodeError):
        return defaults


def save_settings(settings: dict) -> None:
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS_PATH.write_text(json.dumps(settings, indent=2), encoding="utf-8")


def get_by_path(data: dict, path: str, fallback: Any = None) -> Any:
    current = data
    for part in path.split("."):
        if not isinstance(current, dict) or part not in current:
            return fallback
        current = current[part]
    return current


def set_by_path(data: dict, path: str, value: Any) -> None:
    current = data
    parts = path.split(".")
    for part in parts[:-1]:
        if part not in current or not isinstance(current[part], dict):
            current[part] = {}
        current = current[part]
    current[parts[-1]] = value
