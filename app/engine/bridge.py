"""Runs a blocking engine generator on a worker thread and exposes it as an async iterator.
Closing the iterator (client disconnected, Stop pressed) sets a cancel flag so generation stops mid-answer."""
import asyncio
import contextlib
import threading
from typing import AsyncIterator

from .base import Chunk, Engine, GenParams

_DONE = object()


async def astream(engine: Engine, messages: list[dict], params: GenParams) -> AsyncIterator[Chunk]:
    loop = asyncio.get_running_loop()
    queue: asyncio.Queue = asyncio.Queue()
    cancel = threading.Event()

    def worker() -> None:
        try:
            for chunk in engine.stream_chat(messages, params, cancel):
                loop.call_soon_threadsafe(queue.put_nowait, chunk)
        except BaseException as exc:  # forwarded to the consumer
            loop.call_soon_threadsafe(queue.put_nowait, exc)
        finally:
            loop.call_soon_threadsafe(queue.put_nowait, _DONE)

    future = loop.run_in_executor(None, worker)
    try:
        while True:
            item = await queue.get()
            if item is _DONE:
                return
            if isinstance(item, BaseException):
                raise item
            yield item
    finally:
        cancel.set()
        with contextlib.suppress(Exception):
            await future
