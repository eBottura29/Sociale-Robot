import random
import threading

from config import LLM_MODEL_NAME, SENTIMENT_MODEL_NAME


class LlmEngine:
    def __init__(self, debug_cb=None) -> None:
        self.generator = None
        self.sentiment = None
        self.models_ready = False
        self.model_error = ""
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
                    max_new_tokens=60,
                    do_sample=True,
                    temperature=0.7,
                    top_p=0.9,
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
            tokenizer = AutoTokenizer.from_pretrained(LLM_MODEL_NAME)
            model = AutoModelForCausalLM.from_pretrained(LLM_MODEL_NAME)
            self.generator = pipeline("text-generation", model=model, tokenizer=tokenizer, device=-1)
            self.sentiment = pipeline("sentiment-analysis", model=SENTIMENT_MODEL_NAME, device=-1)
            self.models_ready = True
        except Exception as exc:
            self.model_error = f"Model laden faalde: {exc}"
            self._debug(self.model_error)

    def _fallback_response(self, message: str) -> str:
        lowered = message.lower()
        rng = random.Random()
        rng.seed(lowered)

        greetings = [
            "Hoi! Ik ben NIER. Hoe voel je je vandaag?",
            "Hallo! Fijn je te zien. Hoe gaat het met je?",
            "Hey! Ik ben NIER. Waar kan ik je mee helpen?",
            "Hoi daar! Wil je vertellen hoe je je voelt?",
        ]
        empathy = [
            "Dat klinkt moeilijk. Ik ben hier om te luisteren.",
            "Dat is niet makkelijk. Wil je er wat meer over vertellen?",
            "Ik hoor je. Wat speelt er op dit moment?",
            "Dank je dat je dit deelt. Wat heb je nu nodig?",
        ]
        prompts = [
            "Ik luister. Vertel me meer.",
            "Ik ben benieuwd. Kun je dat uitleggen?",
            "Wat bedoel je precies? Ik luister.",
            "Wil je een voorbeeld geven?",
        ]

        if any(word in lowered for word in ["hoi", "hey", "hallo", "goedemorgen", "goeiemorgen", "goeiedag", "goedenavond"]):
            return rng.choice(greetings)
        if any(word in lowered for word in ["eenzaam", "verdrietig", "somber", "bang", "gestrest", "moe", "pijn"]):
            return rng.choice(empathy)
        return rng.choice(prompts)

    def _debug(self, message: str) -> None:
        if self.debug_cb:
            self.debug_cb(message)
