import copy
import sys
from pathlib import Path


SETTINGS_DIR = Path(__file__).resolve().parents[2] / "settings"
if str(SETTINGS_DIR) not in sys.path:
    sys.path.insert(0, str(SETTINGS_DIR))

from settings import load_settings, save_settings


MATRIX_SEGMENTS = 3
MATRIX_ROWS = 8
MATRIX_COLS = MATRIX_SEGMENTS * 8

_LEGACY_8X8 = {
    "Happiness": [0, 66, 165, 129, 165, 153, 66, 60],
    "Fatigue": [0, 195, 165, 129, 165, 129, 66, 60],
    "Hunger": [24, 60, 126, 255, 255, 126, 60, 24],
    "Sadness": [0, 66, 165, 129, 153, 165, 66, 60],
    "Anxiety": [60, 66, 165, 153, 129, 165, 66, 60],
    "Affection": [0, 66, 165, 153, 153, 165, 66, 60],
    "Curiosity": [24, 36, 66, 165, 129, 66, 36, 24],
    "Frustration": [255, 129, 189, 165, 165, 189, 129, 255],
}


def _blank_segments() -> list[list[int]]:
    return [[0 for _ in range(MATRIX_ROWS)] for _ in range(MATRIX_SEGMENTS)]


def _seed_for_emotion(emotion: str) -> list[list[int]]:
    segments = _blank_segments()
    rows = _LEGACY_8X8.get(emotion)
    if rows:
        segments[1] = [int(v) & 0xFF for v in rows]
    return segments


def default_patterns_for_emotions(emotions: list[str]) -> dict[str, list[list[int]]]:
    return {emotion: _seed_for_emotion(emotion) for emotion in emotions}


def _normalize_segment_rows(rows) -> list[int]:
    out = [0 for _ in range(MATRIX_ROWS)]
    if not isinstance(rows, list):
        return out
    for i in range(min(len(rows), MATRIX_ROWS)):
        try:
            out[i] = max(0, min(255, int(rows[i])))
        except (TypeError, ValueError):
            out[i] = 0
    return out


def _normalize_emotion_segments(value) -> list[list[int]]:
    normalized = _blank_segments()
    if not isinstance(value, list):
        return normalized
    for seg in range(min(len(value), MATRIX_SEGMENTS)):
        normalized[seg] = _normalize_segment_rows(value[seg])
    return normalized


def normalize_patterns(raw_patterns, emotions: list[str]) -> dict[str, list[list[int]]]:
    defaults = default_patterns_for_emotions(emotions)
    out = {}
    for emotion in emotions:
        raw = raw_patterns.get(emotion) if isinstance(raw_patterns, dict) else None
        if raw is None:
            out[emotion] = defaults[emotion]
        else:
            out[emotion] = _normalize_emotion_segments(raw)
    return out


def load_led_matrix_patterns(emotions: list[str]) -> dict[str, list[list[int]]]:
    settings = load_settings()
    desktop = settings.get("desktop_app", {})
    led_matrix = desktop.get("led_matrix", {})
    raw = led_matrix.get("patterns_by_emotion", {})
    return normalize_patterns(raw, emotions)


def save_led_matrix_patterns(patterns_by_emotion: dict[str, list[list[int]]], emotions: list[str]) -> None:
    normalized = normalize_patterns(patterns_by_emotion, emotions)
    settings = load_settings()
    desktop = settings.setdefault("desktop_app", {})
    led_matrix = desktop.setdefault("led_matrix", {})
    led_matrix["patterns_by_emotion"] = normalized
    save_settings(settings)


def blank_pattern() -> list[list[int]]:
    return _blank_segments()


def blank_patterns_for_emotions(emotions: list[str]) -> dict[str, list[list[int]]]:
    return {emotion: blank_pattern() for emotion in emotions}


def segments_to_grid(segments: list[list[int]]) -> list[list[int]]:
    grid = [[0 for _ in range(MATRIX_COLS)] for _ in range(MATRIX_ROWS)]
    norm = _normalize_emotion_segments(segments)
    for seg in range(MATRIX_SEGMENTS):
        for y in range(MATRIX_ROWS):
            row_byte = norm[seg][y]
            for x in range(8):
                bit = (row_byte >> (7 - x)) & 0x01
                grid[y][seg * 8 + x] = bit
    return grid


def grid_to_segments(grid: list[list[int]]) -> list[list[int]]:
    segments = _blank_segments()
    for seg in range(MATRIX_SEGMENTS):
        for y in range(MATRIX_ROWS):
            row_val = 0
            if y < len(grid):
                row = grid[y]
                for x in range(8):
                    gx = seg * 8 + x
                    bit = 1 if gx < len(row) and row[gx] else 0
                    row_val = (row_val << 1) | bit
            segments[seg][y] = row_val
    return segments


def _rows_to_matrix(rows: list[int]) -> list[list[int]]:
    matrix = [[0 for _ in range(8)] for _ in range(8)]
    for y in range(8):
        row_byte = rows[y]
        for x in range(8):
            matrix[y][x] = (row_byte >> (7 - x)) & 0x01
    return matrix


def _matrix_to_rows(matrix: list[list[int]]) -> list[int]:
    rows = [0 for _ in range(8)]
    for y in range(8):
        row_val = 0
        for x in range(8):
            row_val = (row_val << 1) | (1 if matrix[y][x] else 0)
        rows[y] = row_val
    return rows


def _rotate_left_8x8(rows: list[int]) -> list[int]:
    src = _rows_to_matrix(rows)
    rotated = [[0 for _ in range(8)] for _ in range(8)]
    for y in range(8):
        for x in range(8):
            rotated[y][x] = src[x][7 - y]
    return _matrix_to_rows(rotated)


def matrix_commands_for_emotion(
    emotion: str, patterns_by_emotion: dict[str, list[list[int]]], compensate_rotation: bool = True
) -> list[str]:
    if emotion not in patterns_by_emotion:
        return []
    segments = _normalize_emotion_segments(copy.deepcopy(patterns_by_emotion[emotion]))
    commands = []
    # Logical order in settings/UI is left, center, right.
    # Hardware send order is flipped for outer matrices: right, center, left.
    segment_tx_index = [2, 1, 0]
    for seg_idx, rows in enumerate(segments):
        payload_rows = _rotate_left_8x8(rows) if compensate_rotation else rows
        csv = ",".join(str(v) for v in payload_rows)
        commands.append(f"MATRIX:{segment_tx_index[seg_idx]},{csv}")
    return commands
