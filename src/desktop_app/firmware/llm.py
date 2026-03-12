import os
import random
import threading
import traceback
import types
from pathlib import Path

from config import (
    LLM_MODEL_NAME,
    SENTIMENT_MODEL_NAME,
    LLM_ALLOW_DOWNLOAD,
    LLM_MAX_NEW_TOKENS,
    LLM_MIN_NEW_TOKENS,
    LLM_REPETITION_PENALTY,
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
            "Stijl: informeel, warm, menselijk. Spreek de gebruiker met 'je/jij' aan.\n"
            "Regels: blijf bij wat de gebruiker zegt; verzin geen feiten; geen rare herhaling.\n"
            "Vermijd formele woorden of plechtige zinnen. Gebruik hoofdletters en leestekens op de juiste plaats.\n"
            "Antwoord direct op de vraag.\n"
            "Formaat: maximaal 1-2 zinnen, maximaal 20 woorden. Geen afgebroken zinnen.\n\n"
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
                    min_new_tokens=LLM_MIN_NEW_TOKENS,
                    do_sample=True,
                    temperature=LLM_TEMPERATURE,
                    top_p=LLM_TOP_P,
                    repetition_penalty=LLM_REPETITION_PENALTY,
                )
            generated = output[0]["generated_text"]
            reply = generated[len(prompt) :].strip()
            if not reply:
                return self._error_response()
            dutch = reply.split("\n")[0].strip()
            return self._truncate_reply(dutch)
        except Exception as exc:
            self._debug(f"LLM_ERROR: {exc}")
            self._debug(f"TRACE:{traceback.format_exc()}")
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
            # Disable torch dynamo/compile paths inside packaged app to avoid torch._numpy issues.
            os.environ.setdefault("TORCH_DISABLE_DYNAMO", "1")
            os.environ.setdefault("TORCHDYNAMO_DISABLE", "1")
            os.environ.setdefault("TORCH_COMPILE_DISABLE", "1")
            self._install_torch_dynamo_stub()
            from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
        except Exception as exc:
            self.model_error = f"Transformers niet beschikbaar: {exc}"
            self._debug(self.model_error)
            self._debug(f"TRACE:{traceback.format_exc()}")
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
            self._debug(f"TRACE:{traceback.format_exc()}")

    def _load_hf_token(self) -> str:
        env_token = os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACE_TOKEN")
        if env_token:
            return env_token.strip()
        try:
            token_path = self._token_dir() / ".hf_token"
            if token_path.exists():
                token = token_path.read_text(encoding="utf-8").strip()
                return token
            token = self._prompt_for_token(token_path)
            if token:
                return token
        except Exception:
            return ""
        return ""

    def _token_dir(self) -> Path:
        return Path.cwd()

    def _install_torch_dynamo_stub(self) -> None:
        """Prevent torch._dynamo imports in frozen builds (avoids torch._numpy crash)."""
        import sys

        if "torch._dynamo" in sys.modules:
            return

        def _false() -> bool:
            return False

        def _disable(fn=None, recursive=False, reason=None, *args, **kwargs):
            if fn is None:
                def decorator(inner):
                    return inner
                return decorator
            return fn

        def _allow_in_graph(fn=None):
            if fn is None:
                def decorator(inner):
                    return inner
                return decorator
            return fn

        def _graph_break(*args, **kwargs):
            return None

        def _mark_dynamic(*args, **kwargs):
            return None

        def _mark_static(*args, **kwargs):
            return None

        dynamo_mod = types.ModuleType("torch._dynamo")
        dynamo_mod.__path__ = []
        dynamo_mod.is_compiling = _false
        dynamo_mod.is_exporting = _false
        dynamo_mod.disable = _disable
        dynamo_mod.allow_in_graph = _allow_in_graph
        dynamo_mod.graph_break = _graph_break
        dynamo_mod.mark_dynamic = _mark_dynamic
        dynamo_mod.mark_static = _mark_static
        sys.modules.setdefault("torch._dynamo", dynamo_mod)

        trace_mod = types.ModuleType("torch._dynamo._trace_wrapped_higher_order_op")

        class TransformGetItemToIndex:
            def __call__(self, *args, **kwargs):
                return None

        trace_mod.TransformGetItemToIndex = TransformGetItemToIndex
        sys.modules.setdefault("torch._dynamo._trace_wrapped_higher_order_op", trace_mod)
        dynamo_mod._trace_wrapped_higher_order_op = trace_mod

    def _prompt_for_token(self, token_path: Path) -> str:
        try:
            import tkinter as tk
            from tkinter import simpledialog
        except Exception:
            return ""
        root = tk._default_root
        temp_root = None
        if root is None:
            temp_root = tk.Tk()
            temp_root.withdraw()
            root = temp_root
        try:
            token = simpledialog.askstring(
                "Hugging Face token",
                "Plak je Hugging Face token.\n"
                "Het wordt opgeslagen als .hf_token in de huidige map.",
                parent=root,
            )
            if token:
                token = token.strip()
                if token:
                    token_path.write_text(token, encoding="utf-8")
                    return token
        finally:
            if temp_root is not None:
                temp_root.destroy()
        return ""

    def _error_response(self) -> str:
        code = 1
        detail = self.model_error or "LLM niet beschikbaar."
        self._debug(f"{code}: {detail}")
        return f"ERROR CODE {code} - Check log voor details."

    def _truncate_reply(self, text: str) -> str:
        if not text:
            return text
        parts = []
        for chunk in text.replace("!", ".").replace("?", ".").split("."):
            chunk = chunk.strip()
            if chunk:
                parts.append(chunk)
            if len(parts) >= 2:
                break
        if parts:
            text = ". ".join(parts).strip()
            if not text.endswith("."):
                text += "."
        words = text.split()
        if len(words) > 20:
            text = " ".join(words[:20]).rstrip()
            if not text.endswith("."):
                text += "."
        lowered = text.lower().strip()
        if lowered.endswith("wil je dat."):
            text = text[:-1] + "?"
        if lowered.endswith("wil je dat"):
            text = text + "?"
        if lowered.endswith("ik wil"):
            text = text + "..."
        return text

    def _debug(self, message: str) -> None:
        if self.debug_cb:
            self.debug_cb(message)
