import gc
import re
import threading
from typing import Iterator

from ..core.errors import AppError
from .base import Chunk, Engine, GenParams, LoadSpec

# Filename hint -> llama-cpp-python multimodal chat handler. Override per preset with `vision_handler`.
_VISION_HANDLERS = [
    # SmolVLM GGUFs use llama.cpp's mtmd multimodal backend and embedded chat template.
    (r"smolvlm", "MTMDChatHandler"),
    (r"qwen3[-_.]?vl", "Qwen3VLChatHandler"),
    (r"qwen2[-_.]?5[-_.]?vl", "Qwen25VLChatHandler"),
    (r"gemma[-_.]?3", "Gemma3ChatHandler"),
    (r"minicpm", "MiniCPMv26ChatHandler"),
    (r"moondream", "MoondreamChatHandler"),
    (r"llava[-_.]?(1[-_.]?6|v1[-_.]?6)", "Llava16ChatHandler"),
]


class LlamaCppEngine(Engine):
    name = "llama_cpp"

    def __init__(self) -> None:
        self._llm = None
        self.supports_vision = False

    def _vision_handler(self, spec: LoadSpec):
        from llama_cpp import llama_chat_format as fmt

        wanted = spec.vision_handler
        if not wanted:
            low = spec.path.lower()
            wanted = next((cls for pat, cls in _VISION_HANDLERS if re.search(pat, low)), "Llava15ChatHandler")
        handler = getattr(fmt, wanted, None)
        if handler is None:
            raise AppError(400, "vision_handler_unavailable",
                           f"This llama-cpp-python build has no '{wanted}'. Upgrade it or set another vision_handler.")
        return handler(clip_model_path=spec.mmproj_path)

    def load(self, spec: LoadSpec) -> None:
        try:
            from llama_cpp import Llama
        except ImportError as exc:
            raise AppError(500, "engine_missing",
                           "llama-cpp-python is not installed. Run: pip install -r requirements-engine.txt") from exc
        kwargs = dict(model_path=spec.path, n_ctx=spec.n_ctx, n_gpu_layers=spec.n_gpu_layers, n_batch=spec.n_batch,
                      flash_attn=spec.flash_attn, use_mmap=spec.use_mmap, use_mlock=spec.use_mlock, verbose=False)
        if spec.n_threads:
            kwargs["n_threads"] = spec.n_threads
        if spec.chat_format:
            kwargs["chat_format"] = spec.chat_format
        if spec.mmproj_path:
            kwargs["chat_handler"] = self._vision_handler(spec)
        try:
            self._llm = Llama(**kwargs)
        except Exception as exc:  # llama.cpp raises bare ValueError/RuntimeError for bad files or OOM
            raise AppError(400, "load_failed", f"Could not load the model: {exc}") from exc
        self.supports_vision = bool(spec.mmproj_path)

    def unload(self) -> None:
        llm, self._llm = self._llm, None
        if llm is not None and hasattr(llm, "close"):
            llm.close()
        del llm
        gc.collect()
        self.supports_vision = False

    def count_tokens(self, text: str) -> int:
        if self._llm is None:
            return max(1, len(text) // 4)
        return len(self._llm.tokenize(text.encode("utf-8"), add_bos=False))

    def stream_chat(self, messages: list[dict], params: GenParams, cancel: threading.Event) -> Iterator[Chunk]:
        kw = dict(messages=messages, stream=True, temperature=params.temperature, top_p=params.top_p,
                  top_k=params.top_k, min_p=params.min_p, max_tokens=params.max_tokens,
                  repeat_penalty=params.repeat_penalty, stop=params.stop)
        if params.seed is not None:
            kw["seed"] = params.seed
        if params.response_schema:
            kw["response_format"] = {"type": "json_object", "schema": params.response_schema}
        gen = self._llm.create_chat_completion(**kw)
        finish = None
        try:
            for part in gen:
                if cancel.is_set():
                    break
                choice = part["choices"][0]
                text = (choice.get("delta") or {}).get("content") or ""
                if text:
                    yield Chunk(text=text)
                finish = choice.get("finish_reason") or finish
        finally:
            gen.close()
        yield Chunk(finish_reason="cancelled" if cancel.is_set() else (finish or "stop"))
