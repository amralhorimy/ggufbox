import threading
import time
from typing import Iterator

from .base import Chunk, Engine, GenParams, LoadSpec


class MockEngine(Engine):
    """Streams a canned reply (with a <think> block). Lets you try the whole app, or run tests, with no model."""

    name = "mock"

    def __init__(self) -> None:
        self._spec: LoadSpec | None = None
        self.supports_vision = False

    def load(self, spec: LoadSpec) -> None:
        self._spec = spec
        self.supports_vision = bool(spec.mmproj_path)

    def unload(self) -> None:
        self._spec, self.supports_vision = None, False

    def count_tokens(self, text: str) -> int:
        return max(1, len(text.split()))

    def stream_chat(self, messages: list[dict], params: GenParams, cancel: threading.Event) -> Iterator[Chunk]:
        last = messages[-1]["content"]
        if isinstance(last, list):
            last = " ".join(p.get("text", "") for p in last if p.get("type") == "text")
        if params.response_schema:
            reply = '{"echo": "' + last[:40].replace('"', "'").replace("\n", " ") + '"}'
        else:
            reply = f"<think>The user wrote {len(last.split())} words.</think>Mock reply to: {last[:200]}"
        for word in reply.split(" "):
            if cancel.is_set():
                yield Chunk(finish_reason="cancelled")
                return
            yield Chunk(text=word + " ")
            time.sleep(0.01)
        yield Chunk(finish_reason="stop")
