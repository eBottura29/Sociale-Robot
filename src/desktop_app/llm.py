import threading

from config import (
    LLM_MODEL_NAME,
    SENTIMENT_MODEL_NAME,
    TRANSLATION_MODEL_NAME,
    TRANSLATION_SRC_LANG,
    TRANSLATION_TGT_LANG,
    TRANSLATION_BACK_LANG,
)


class LlmEngine:
    def __init__(self, debug_cb=None) -> None:
        self.generator = None
        self.sentiment = None
        self.translation_tokenizer = None
        self.translation_model = None
        self.models_ready = False
        self.model_error = ""
        self.model_lock = threading.Lock()
        self.debug_cb = debug_cb

    def generate_response(self, message: str) -> str:
        self._ensure_models()
        if not self.models_ready or self.generator is None:
            return self._fallback_response(message)
        translated = self._translate_nl_to_en(message)
        prompt = (
            "System: You are NIER, a friendly social robot. Respond in English.\n"
            f"User: {translated}\n"
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
            english = reply.split("\n")[0].strip()
            return self._translate_en_to_nl(english)
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
            from transformers import AutoModelForCausalLM, AutoModelForSeq2SeqLM, AutoTokenizer, pipeline
        except Exception as exc:
            self.model_error = f"Transformers niet beschikbaar: {exc}"
            self._debug(self.model_error)
            return
        try:
            tokenizer = AutoTokenizer.from_pretrained(LLM_MODEL_NAME)
            model = AutoModelForCausalLM.from_pretrained(LLM_MODEL_NAME)
            self.generator = pipeline("text-generation", model=model, tokenizer=tokenizer, device=-1)
            self.sentiment = pipeline("sentiment-analysis", model=SENTIMENT_MODEL_NAME, device=-1)
            self.translation_tokenizer = AutoTokenizer.from_pretrained(TRANSLATION_MODEL_NAME)
            self.translation_model = AutoModelForSeq2SeqLM.from_pretrained(TRANSLATION_MODEL_NAME)
            self.models_ready = True
        except Exception as exc:
            self.model_error = f"Model laden faalde: {exc}"
            self._debug(self.model_error)

    def _fallback_response(self, message: str) -> str:
        lowered = message.lower()
        if any(word in lowered for word in ["hoi", "hey", "hallo"]):
            return "Hoi! Ik ben NIER. Hoe voel je je vandaag?"
        if "eenzaam" in lowered:
            return "Dat klinkt moeilijk. Ik ben hier om te luisteren."
        return "Ik luister. Vertel me meer."

    def _translate_nl_to_en(self, text: str) -> str:
        if not self.translation_model or not self.translation_tokenizer:
            return text
        try:
            with self.model_lock:
                self.translation_tokenizer.src_lang = TRANSLATION_SRC_LANG
                encoded = self.translation_tokenizer(text, return_tensors="pt")
                generated = self.translation_model.generate(
                    **encoded,
                    forced_bos_token_id=self.translation_tokenizer.lang_code_to_id[TRANSLATION_TGT_LANG],
                    max_new_tokens=128,
                )
                return self.translation_tokenizer.batch_decode(generated, skip_special_tokens=True)[0]
        except Exception:
            return text

    def _translate_en_to_nl(self, text: str) -> str:
        if not self.translation_model or not self.translation_tokenizer:
            return text
        try:
            with self.model_lock:
                self.translation_tokenizer.src_lang = TRANSLATION_TGT_LANG
                encoded = self.translation_tokenizer(text, return_tensors="pt")
                generated = self.translation_model.generate(
                    **encoded,
                    forced_bos_token_id=self.translation_tokenizer.lang_code_to_id[TRANSLATION_BACK_LANG],
                    max_new_tokens=128,
                )
                return self.translation_tokenizer.batch_decode(generated, skip_special_tokens=True)[0]
        except Exception:
            return text

    def _debug(self, message: str) -> None:
        if self.debug_cb:
            self.debug_cb(message)
