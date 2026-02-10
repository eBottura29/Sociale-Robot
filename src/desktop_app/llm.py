import random
import threading
import os
from pathlib import Path

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

    def generate_response(
        self, message: str, history: list | None = None, emotions: dict | None = None
    ) -> str:
        self._ensure_models()
        if not self.models_ready or self.generator is None:
            return self._error_response()
        history = history or []
        emotions = emotions or {}
        emotion_lines = (
            ", ".join([f"{name}={value}%" for name, value in emotions.items()]) or "onbekend"
        )
        dominant = "onbekend"
        if emotions:
            dominant = max(emotions.items(), key=lambda kv: kv[1])[0]
        history_text = "\n".join(history).strip()
        prompt = (
            "System:\n"
            "Je bent NIER, een vriendelijke sociale robot. Antwoord altijd in het Nederlands.\n"
            "Stijl: empathisch, duidelijk, natuurlijk. Stel af en toe een korte vervolgvraag.\n"
            "Regels: blijf bij wat de gebruiker zegt; verzin geen feiten. Houd antwoorden beknopt.\n\n"
            f"Emoties (percentages): {emotion_lines}\n"
            f"Dominante emotie: {dominant}\n\n"
            "Gespreksgeschiedenis:\n"
            f"{history_text}\n\n"
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
            reply = generated[len(prompt) :].strip()
            if not reply:
                return self._error_response()
            dutch = reply.split("\n")[0].strip()
            return dutch
        except Exception:
            return self._error_response()

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
            token = self._load_hf_token()
            kwargs = {"local_files_only": local_only}
            if token:
                kwargs["token"] = token
            tokenizer = AutoTokenizer.from_pretrained(LLM_MODEL_NAME, **kwargs)
            model = AutoModelForCausalLM.from_pretrained(LLM_MODEL_NAME, **kwargs)
            self.generator = pipeline(
                "text-generation", model=model, tokenizer=tokenizer, device=-1
            )
            sent_kwargs = {
                "model": SENTIMENT_MODEL_NAME,
                "device": -1,
                "local_files_only": local_only,
            }
            if token:
                sent_kwargs["token"] = token
            self.sentiment = pipeline("sentiment-analysis", **sent_kwargs)
            self.models_ready = True
        except Exception as exc:
            if not LLM_ALLOW_DOWNLOAD:
                self.model_error = "LLM niet beschikbaar (offline of model niet lokaal)."
            else:
                self.model_error = f"Model laden faalde: {exc}"
            self._debug(self.model_error)

    def _load_hf_token(self) -> str:
        env_token = os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACE_TOKEN")
        if env_token:
            return env_token.strip()
        try:
            base_dir = Path(__file__).resolve().parents[2]
            token_path = base_dir / ".hf_token"
            if token_path.exists():
                token = token_path.read_text(encoding="utf-8").strip()
                return token
        except Exception:
            return ""
        return ""

    def _error_response(self) -> str:
        code = 1
        detail = self.model_error or "LLM niet beschikbaar."
        self._debug(f"{code}: {detail}")
        return f"ERROR CODE {code} - Check log voor details."

    def _debug(self, message: str) -> None:
        if self.debug_cb:
            self.debug_cb(message)
