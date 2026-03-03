import sys
from pathlib import Path


SETTINGS_DIR = Path(__file__).resolve().parents[1] / "settings"
if str(SETTINGS_DIR) not in sys.path:
    sys.path.insert(0, str(SETTINGS_DIR))

from settings import load_settings


def _default_for_emotions(emotions: list[str]) -> dict[str, tuple[int, int]]:
    return {emotion: (90, 90) for emotion in emotions}


def load_eyebrow_angles(emotions: list[str]) -> dict[str, tuple[int, int]]:
    settings = load_settings()
    raw = (
        settings.get("robot", {})
        .get("defaults", {})
        .get("eyebrow_angles_by_emotion", {})
    )
    result = _default_for_emotions(emotions)
    if not isinstance(raw, dict):
        return result

    for emotion in emotions:
        key = emotion.upper()
        value = raw.get(key)
        if isinstance(value, list) and len(value) >= 2:
            try:
                left = max(0, min(180, int(value[0])))
                right = max(0, min(180, int(value[1])))
                result[emotion] = (left, right)
            except (TypeError, ValueError):
                result[emotion] = (90, 90)
    return result


def browmap_command_for_emotion(emotion: str, emotions: list[str], angles: dict[str, tuple[int, int]]) -> str | None:
    if emotion not in emotions:
        return None
    index = emotions.index(emotion)
    left, right = angles.get(emotion, (90, 90))
    left = max(0, min(180, int(left)))
    right = max(0, min(180, int(right)))
    return f"BROWMAP:{index},{left},{right}"
