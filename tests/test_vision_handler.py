import sys
import types

from app.engine.base import LoadSpec
from app.engine.llama_cpp_engine import LlamaCppEngine


def test_smolvlm_selects_mtmd_handler_with_projector(monkeypatch):
    seen = {}

    class FakeMTMDChatHandler:
        def __init__(self, clip_model_path):
            seen["clip_model_path"] = clip_model_path

    fake_format = types.ModuleType("llama_cpp.llama_chat_format")
    fake_format.MTMDChatHandler = FakeMTMDChatHandler
    fake_llama_cpp = types.ModuleType("llama_cpp")
    fake_llama_cpp.llama_chat_format = fake_format
    monkeypatch.setitem(sys.modules, "llama_cpp", fake_llama_cpp)

    spec = LoadSpec(
        path="/models/SmolVLM-500M-Instruct-Q8_0.gguf",
        mmproj_path="/models/mmproj-SmolVLM-500M-Instruct-Q8_0.gguf",
    )
    handler = LlamaCppEngine()._vision_handler(spec)

    assert isinstance(handler, FakeMTMDChatHandler)
    assert seen["clip_model_path"] == spec.mmproj_path
