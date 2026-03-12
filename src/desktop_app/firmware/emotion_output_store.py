from settings_loader import load_settings


_DEFAULT_RGB = {
    "Happiness": (0, 220, 80),
    "Fatigue": (40, 40, 180),
    "Hunger": (255, 140, 0),
    "Sadness": (0, 90, 220),
    "Anxiety": (255, 200, 0),
    "Affection": (255, 80, 140),
    "Curiosity": (0, 220, 220),
    "Frustration": (255, 30, 30),
}

_DEFAULT_BUZZER = {
    "Happiness": 1400,
    "Fatigue": 0,
    "Hunger": 900,
    "Sadness": 0,
    "Anxiety": 1850,
    "Affection": 1200,
    "Curiosity": 1300,
    "Frustration": 2200,
}


def _rgb_for_emotions(emotions: list[str]) -> dict[str, tuple[int, int, int]]:
    return {emotion: _DEFAULT_RGB.get(emotion, (0, 0, 0)) for emotion in emotions}


def _buzzer_for_emotions(emotions: list[str]) -> dict[str, int]:
    return {emotion: int(_DEFAULT_BUZZER.get(emotion, 0)) for emotion in emotions}


def load_emotion_rgb_map(emotions: list[str]) -> dict[str, tuple[int, int, int]]:
    settings = load_settings()
    raw = settings.get("desktop_app", {}).get("emotion_rgb_by_emotion", {})
    result = _rgb_for_emotions(emotions)
    if not isinstance(raw, dict):
        return result
    for emotion in emotions:
        value = raw.get(emotion)
        if isinstance(value, list) and len(value) >= 3:
            try:
                r = max(0, min(255, int(value[0])))
                g = max(0, min(255, int(value[1])))
                b = max(0, min(255, int(value[2])))
                result[emotion] = (r, g, b)
            except (TypeError, ValueError):
                continue
    return result


def load_emotion_buzzer_pitch_map(emotions: list[str]) -> dict[str, int]:
    settings = load_settings()
    raw = settings.get("desktop_app", {}).get("emotion_buzzer_pitch_by_emotion", {})
    result = _buzzer_for_emotions(emotions)
    if not isinstance(raw, dict):
        return result
    for emotion in emotions:
        value = raw.get(emotion)
        try:
            result[emotion] = max(0, min(5000, int(value)))
        except (TypeError, ValueError):
            continue
    return result
