"""Stateless generation: messages in, (reasoning | content) stream out. Shared by chats, /v1 and virtual APIs."""
import time
from contextlib import aclosing
from typing import AsyncIterator

from ..engine import GenParams
from ..schemas import GenSettings
from .model_manager import ModelManager
from .thinking import ThinkingSplitter


class CompletionService:
    def __init__(self, manager: ModelManager):
        self.manager = manager

    def build_params(self, overrides: dict, response_schema: dict | None = None, *extra: dict) -> GenParams:
        """Precedence (low -> high): preset defaults of the loaded model, `extra` dicts in order, `overrides`."""
        defaults = self.manager.current.gen_defaults if self.manager.current else {}
        merged: dict = dict(defaults)
        for layer in (*extra, overrides):
            merged.update({k: v for k, v in layer.items() if v is not None})
        return GenParams(**GenSettings.model_validate(merged).model_dump(), response_schema=response_schema)

    async def stream(self, messages: list[dict], params: GenParams, *, prefilled: bool = False,
                     ) -> AsyncIterator[tuple[str, object]]:
        """Yields ("content"|"reasoning", text) and finally ("finish", {finish_reason, completion_tokens, seconds})."""
        splitter, started, count, finish = ThinkingSplitter(prefilled), time.monotonic(), 0, "stop"
        async with aclosing(self.manager.generate(messages, params)) as chunks:
            async for chunk in chunks:
                if chunk.text:
                    count += 1
                    for kind, text in splitter.feed(chunk.text):
                        yield kind, text
                if chunk.finish_reason:
                    finish = chunk.finish_reason
        for kind, text in splitter.flush():
            yield kind, text
        yield "finish", {"finish_reason": finish, "completion_tokens": count,
                         "seconds": round(time.monotonic() - started, 3)}

    async def collect(self, messages: list[dict], params: GenParams, *, prefilled: bool = False) -> dict:
        content, reasoning, info = [], [], {}
        async with aclosing(self.stream(messages, params, prefilled=prefilled)) as events:
            async for kind, value in events:
                if kind == "content":
                    content.append(value)
                elif kind == "reasoning":
                    reasoning.append(value)
                else:
                    info = value
        return {"content": "".join(content).strip(), "reasoning": "".join(reasoning).strip(), **info}
