"""The seam between the app and any inference backend. Everything above this file is engine-agnostic."""
import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Iterator


@dataclass
class LoadSpec:
    path: str
    mmproj_path: str | None = None
    n_ctx: int = 4096
    n_gpu_layers: int = 0
    n_threads: int | None = None
    n_batch: int = 512
    flash_attn: bool = False
    use_mmap: bool = True
    use_mlock: bool = False
    vision_handler: str | None = None
    chat_format: str | None = None


@dataclass
class GenParams:
    temperature: float = 0.7
    top_p: float = 0.95
    top_k: int = 40
    min_p: float = 0.05
    max_tokens: int = 1024
    repeat_penalty: float = 1.1
    seed: int | None = None
    stop: list[str] | None = None
    response_schema: dict | None = None


@dataclass
class Chunk:
    text: str = ""
    finish_reason: str | None = None


class Engine(ABC):
    name = "base"
    supports_vision = False

    @abstractmethod
    def load(self, spec: LoadSpec) -> None: ...

    @abstractmethod
    def unload(self) -> None: ...

    @abstractmethod
    def count_tokens(self, text: str) -> int: ...

    @abstractmethod
    def stream_chat(self, messages: list[dict], params: GenParams, cancel: threading.Event) -> Iterator[Chunk]:
        """Blocking generator. Must stop promptly once `cancel` is set."""
