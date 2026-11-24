from .base import Chunk, Engine, GenParams, LoadSpec


def create_engine(name: str) -> Engine:
    if name == "mock":
        from .mock_engine import MockEngine
        return MockEngine()
    from .llama_cpp_engine import LlamaCppEngine
    return LlamaCppEngine()


__all__ = ["Chunk", "Engine", "GenParams", "LoadSpec", "create_engine"]
