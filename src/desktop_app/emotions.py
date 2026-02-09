from config import EMOTIONS


class EmotionEngine:
    def __init__(self) -> None:
        self.stat_levels = {"Hunger": 0, "Fatigue": 0}

    def reset(self) -> None:
        self.stat_levels["Hunger"] = 0
        self.stat_levels["Fatigue"] = 0

    def compute(self, context_text: str, sentiment_score: int) -> dict:
        values = {name: 10 for name in EMOTIONS}

        happiness = 10 + int(sentiment_score * 15)
        sadness = 70 - int(sentiment_score * 12)
        values["Happiness"] = self._clamp(happiness)
        values["Sadness"] = self._clamp(sadness)

        lowered = context_text.lower()
        self.stat_levels["Hunger"] = self._clamp(self.stat_levels["Hunger"] + 5)
        self.stat_levels["Fatigue"] = self._clamp(self.stat_levels["Fatigue"] + 3)

        if any(word in lowered for word in ["moe", "slaperig"]):
            values["Fatigue"] = 75
            self.stat_levels["Fatigue"] = self._clamp(self.stat_levels["Fatigue"] + 10)
        if any(word in lowered for word in ["honger", "eten"]):
            values["Hunger"] = 70
            self.stat_levels["Hunger"] = self._clamp(self.stat_levels["Hunger"] + 10)
        if any(word in lowered for word in ["bang", "stress", "zenuw"]):
            values["Anxiety"] = 72
        if any(word in lowered for word in ["lief", "dank", "vriend"]):
            values["Affection"] = 68
        if any(word in lowered for word in ["nieuw", "wat", "hoe", "?"]):
            values["Curiosity"] = 60
        if any(word in lowered for word in ["boos", "frustr", "irrit"]):
            values["Frustration"] = 70

        values["Hunger"] = max(values["Hunger"], self.stat_levels["Hunger"])
        values["Fatigue"] = max(values["Fatigue"], self.stat_levels["Fatigue"])

        return {name: self._clamp(value) for name, value in values.items()}

    def _clamp(self, value: int) -> int:
        return max(0, min(100, int(value)))
