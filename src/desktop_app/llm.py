import random
import threading

from config import (
    LLM_MODEL_NAME,
    SENTIMENT_MODEL_NAME,
    LLM_ALLOW_DOWNLOAD,
    LLM_MAX_NEW_TOKENS,
    LLM_TEMPERATURE,
    LLM_TOP_P,
)


class LlmEngine:
    def __init__(self, debug_cb=None) -> None:
        self.generator = None
        self.sentiment = None
        self.models_ready = False
        self.model_error = ""
        self.last_fallback = ""
        self.model_lock = threading.Lock()
        self.debug_cb = debug_cb

    def generate_response(self, message: str) -> str:
        self._ensure_models()
        if not self.models_ready or self.generator is None:
            return self._fallback_response(message)
        prompt = (
            "System: Je bent NIER, een vriendelijke sociale robot. "
            "Antwoord altijd in het Nederlands.\n"
            f"Gebruiker: {message}\n"
            "NIER:"
        )
        try:
            with self.model_lock:
                output = self.generator(
                    prompt,
                    max_new_tokens=LLM_MAX_NEW_TOKENS,
                    do_sample=True,
                    temperature=LLM_TEMPERATURE,
                    top_p=LLM_TOP_P,
                )
            generated = output[0]["generated_text"]
            reply = generated[len(prompt):].strip()
            if not reply:
                return self._fallback_response(message)
            dutch = reply.split("\n")[0].strip()
            return dutch
        except Exception:
            return self._fallback_response(message)

    def sentiment_score(self, text: str) -> int:
        self._ensure_models()
        if not self.models_ready or self.sentiment is None:
            return 2
        try:
            with self.model_lock:
                result = self.sentiment(text[:256])
            label = result[0].get("label", "3 stars")
            digits = "".join(ch for ch in label if ch.isdigit())
            return int(digits) if digits else 3
        except Exception:
            return 3

    def _ensure_models(self) -> None:
        if self.models_ready or self.model_error:
            return
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
        except Exception as exc:
            self.model_error = f"Transformers niet beschikbaar: {exc}"
            self._debug(self.model_error)
            return
        try:
            local_only = not LLM_ALLOW_DOWNLOAD
            tokenizer = AutoTokenizer.from_pretrained(LLM_MODEL_NAME, local_files_only=local_only)
            model = AutoModelForCausalLM.from_pretrained(LLM_MODEL_NAME, local_files_only=local_only)
            self.generator = pipeline("text-generation", model=model, tokenizer=tokenizer, device=-1)
            self.sentiment = pipeline(
                "sentiment-analysis",
                model=SENTIMENT_MODEL_NAME,
                device=-1,
                local_files_only=local_only,
            )
            self.models_ready = True
        except Exception as exc:
            if not LLM_ALLOW_DOWNLOAD:
                self.model_error = "LLM niet beschikbaar (offline of model niet lokaal)."
            else:
                self.model_error = f"Model laden faalde: {exc}"
            self._debug(self.model_error)

    def _fallback_response(self, message: str) -> str:
        lowered = message.lower()
        greetings = [
            "Hoi! Ik ben NIER. Hoe voel je je vandaag?",
            "Hallo! Fijn je te zien. Hoe gaat het met je?",
            "Hey! Ik ben NIER. Waar kan ik je mee helpen?",
            "Hoi daar! Wil je vertellen hoe je je voelt?",
            "Leuk dat je er bent. Wat houdt je bezig?",
            "Welkom terug. Waar wil je over praten?",
        ]
        empathy = [
            "Dat klinkt moeilijk. Ik ben hier om te luisteren.",
            "Dat is niet makkelijk. Wil je er wat meer over vertellen?",
            "Ik hoor je. Wat speelt er op dit moment?",
            "Dank je dat je dit deelt. Wat heb je nu nodig?",
            "Dat kan zwaar zijn. Zal ik gewoon luisteren of wil je advies?",
            "Ik kan me voorstellen dat dat lastig voelt. Vertel gerust verder.",
        ]
        questions = [
            "Ik luister. Vertel me meer.",
            "Ik ben benieuwd. Kun je dat uitleggen?",
            "Wat bedoel je precies? Ik luister.",
            "Wil je een voorbeeld geven?",
            "Hoe begon dit?",
            "Wat is voor jou het belangrijkste hieraan?",
            "Wat hoop je dat er verandert?",
        ]
        thanks = [
            "Graag gedaan! Wil je nog iets vragen?",
            "Geen probleem. Ik ben er voor je.",
            "Fijn dat ik kon helpen. Waar wil je nu verder over praten?",
        ]
        checks = [
            "Oké. Hoe voel je je daarbij?",
            "Ik snap het. Wat wil je nu doen?",
            "Dat is duidelijk. Wil je dat ik meedenk of gewoon luister?",
        ]

        if any(word in lowered for word in ["dank", "merci", "bedankt", "thx"]):
            return self._pick(thanks)
        if any(word in lowered for word in ["hoi", "hey", "hallo", "goedemorgen", "goeiemorgen", "goeiedag", "goedenavond"]):
            return self._pick(greetings)
        if any(word in lowered for word in ["eenzaam", "verdrietig", "somber", "bang", "gestrest", "moe", "pijn", "angst", "stress"]):
            return self._pick(empathy)
        if any(word in lowered for word in ["ja", "ok", "goed", "prima", "gaat", "fijn", "meh"]):
            return self._pick(checks)
        return self._pick(questions)

    def _pick(self, options: list) -> str:
        if not options:
            return ""
        if len(options) == 1:
            self.last_fallback = options[0]
            return options[0]
        candidate = random.choice(options)
        if candidate == self.last_fallback:
            alt = [opt for opt in options if opt != self.last_fallback]
            if alt:
                candidate = random.choice(alt)
        self.last_fallback = candidate
        return candidate

    def _debug(self, message: str) -> None:
        if self.debug_cb:
            self.debug_cb(message)
