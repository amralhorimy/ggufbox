"""Owns the one loaded model: discovery, RAM checks, load/unload, idle unload and serialised generation."""
import asyncio
import re
import time
from contextlib import aclosing
from dataclasses import dataclass, field
from pathlib import Path
from typing import AsyncIterator

from ..config import Settings
from ..core.errors import AppError
from ..core.resources import check_fit, estimate_memory
from ..db.repositories import PresetRepo
from ..engine import Chunk, Engine, GenParams, LoadSpec
from ..engine.bridge import astream
from ..schemas import LoadParams

_SHARD = re.compile(r"-(\d{5})-of-(\d{5})\.gguf$", re.I)
_QUANT = re.compile(r"(I?Q\d(?:_[A-Z0-9]+)*|BF16|F16|F32)", re.I)


@dataclass
class ModelFile:
    filename: str
    size_bytes: int
    mmproj: str | None
    mmproj_bytes: int

    def as_dict(self) -> dict:
        quant = _QUANT.findall(Path(self.filename).stem)
        return {"filename": self.filename, "name": Path(self.filename).stem, "size_bytes": self.size_bytes,
                "quant": quant[-1].upper() if quant else None, "vision": self.mmproj is not None,
                "mmproj": self.mmproj}


@dataclass
class LoadedModel:
    filename: str
    params: dict
    preset_id: str | None
    preset_name: str | None
    options: dict
    gen_defaults: dict
    vision: bool
    estimate: dict
    load_seconds: float
    loaded_at: float = field(default_factory=time.time)

    def as_dict(self) -> dict:
        return {"filename": self.filename, "name": Path(self.filename).stem, "params": self.params,
                "preset_id": self.preset_id, "preset_name": self.preset_name, "vision": self.vision,
                "estimate": self.estimate, "load_seconds": self.load_seconds, "loaded_at": self.loaded_at}


class ModelManager:
    def __init__(self, settings: Settings, engine: Engine, presets: PresetRepo):
        self.settings, self.engine, self.presets = settings, engine, presets
        self.current: LoadedModel | None = None
        self._admin_lock = asyncio.Lock()  # load / unload
        self._gen_lock = asyncio.Lock()    # llama.cpp handles one generation at a time
        self._last_used = time.monotonic()
        self._parked: dict | None = None   # what to reload after an idle unload

    # ---- discovery -------------------------------------------------------------------------
    def scan(self) -> list[ModelFile]:
        root = self.settings.models_dir
        if not root.is_dir():
            return []
        found: list[ModelFile] = []
        for path in sorted(root.rglob("*.gguf")):
            if "mmproj" in path.name.lower():
                continue
            shard = _SHARD.search(path.name)
            if shard and shard.group(1) != "00001":
                continue
            size = path.stat().st_size
            if shard:
                prefix = path.name[: shard.start()]
                size = sum(p.stat().st_size for p in path.parent.glob(f"{prefix}-*-of-{shard.group(2)}.gguf"))
            projectors = sorted(p for p in path.parent.glob("*.gguf") if "mmproj" in p.name.lower())
            proj = projectors[0] if projectors else None
            found.append(ModelFile(path.relative_to(root).as_posix(), size,
                                   proj.relative_to(root).as_posix() if proj else None,
                                   proj.stat().st_size if proj else 0))
        return found

    def find(self, filename: str) -> ModelFile:
        root = self.settings.models_dir.resolve()
        target = (root / filename).resolve()
        if root not in target.parents or target.suffix.lower() != ".gguf":
            raise AppError(404, "model_not_found", f"Model '{filename}' was not found in the models folder.")
        match = next((m for m in self.scan() if m.filename == filename), None)
        if not match:
            raise AppError(404, "model_not_found", f"Model '{filename}' was not found in the models folder.")
        return match

    def estimate(self, filename: str, n_ctx: int, n_gpu_layers: int) -> dict:
        model = self.find(filename)
        est = estimate_memory(model.size_bytes, n_ctx, n_gpu_layers, model.mmproj_bytes)
        return {**est.as_dict(), **check_fit(est, self.settings.ram_budget_fraction)}

    # ---- lifecycle -------------------------------------------------------------------------
    def status(self) -> dict:
        return {"loaded": self.current is not None, "model": self.current.as_dict() if self.current else None,
                "busy": self._gen_lock.locked(), "engine": self.engine.name,
                "idle_unloaded": self._parked is not None and self.current is None}

    async def load_with_preset(self, filename: str, preset_id: str | None, overrides: dict, force: bool = False,
                               ) -> LoadedModel:
        preset = await self.presets.get(preset_id) if preset_id else await self.presets.for_model(filename)
        if preset_id and not preset:
            raise AppError(404, "preset_not_found", "Preset not found.")
        params = LoadParams.model_validate({**(preset["load_params"] if preset else {}), **overrides})
        return await self.load(filename, params, preset, force)

    async def load(self, filename: str, params: LoadParams, preset: dict | None, force: bool = False) -> LoadedModel:
        async with self._admin_lock:
            model = self.find(filename)
            est = estimate_memory(model.size_bytes, params.n_ctx, params.n_gpu_layers, model.mmproj_bytes)
            fit = check_fit(est, self.settings.ram_budget_fraction)
            if not fit["fits"] and not force:
                raise AppError(409, "insufficient_memory",
                               "Loading this model with these settings is estimated to exceed the free RAM budget. "
                               "Lower n_ctx or n_gpu_layers, free memory, or retry with force=true.", fit)
            async with self._gen_lock:  # wait for any running answer to finish
                await self._unload_unlocked()
                root = self.settings.models_dir.resolve()
                spec = LoadSpec(path=str(root / filename),
                                mmproj_path=str(root / model.mmproj) if model.mmproj else None,
                                **params.model_dump())
                started = time.monotonic()
                await asyncio.get_running_loop().run_in_executor(None, self.engine.load, spec)
                self.current = LoadedModel(
                    filename=filename, params=params.model_dump(), preset_id=preset["id"] if preset else None,
                    preset_name=preset["name"] if preset else None, options=preset["options"] if preset else {},
                    gen_defaults=preset["gen_params"] if preset else {}, vision=self.engine.supports_vision,
                    estimate={**est.as_dict(), **fit}, load_seconds=round(time.monotonic() - started, 2))
                self._parked = None
                self._last_used = time.monotonic()
                return self.current

    async def _unload_unlocked(self) -> None:
        if self.current is not None:
            await asyncio.get_running_loop().run_in_executor(None, self.engine.unload)
            self.current = None

    async def unload(self) -> None:
        async with self._admin_lock:
            async with self._gen_lock:
                await self._unload_unlocked()
                self._parked = None

    async def ensure(self, filename: str | None, preset_id: str | None = None) -> None:
        """Make sure the requested model is loaded (loading it on demand if auto_load is on)."""
        if not filename or (self.current and self.current.filename == filename):
            return
        if not self.settings.auto_load:
            raise AppError(409, "model_not_loaded", f"'{filename}' is not loaded and auto-load is disabled.")
        await self.load_with_preset(filename, preset_id, {})

    async def idle_watchdog(self) -> None:
        """Frees RAM after a quiet period; the model is brought back on the next request."""
        while True:
            await asyncio.sleep(10)
            limit = self.settings.idle_unload_seconds
            if limit and self.current and not self._gen_lock.locked() and time.monotonic() - self._last_used > limit:
                parked = {"filename": self.current.filename, "preset_id": self.current.preset_id,
                          "overrides": self.current.params}
                await self.unload()
                self._parked = parked

    # ---- generation ------------------------------------------------------------------------
    def count_tokens(self, text: str) -> int:
        return self.engine.count_tokens(text)

    async def restore(self) -> None:
        """Bring back the model that an idle unload parked."""
        if self.current is None and self._parked:
            p = self._parked
            await self.load_with_preset(p["filename"], p["preset_id"], p["overrides"])

    async def generate(self, messages: list[dict], params: GenParams) -> AsyncIterator[Chunk]:
        await self.restore()
        async with self._gen_lock:
            if self.current is None:
                raise AppError(409, "no_model_loaded", "No model is loaded. Load one from the Models page first.")
            try:
                async with aclosing(astream(self.engine, messages, params)) as stream:
                    async for chunk in stream:
                        yield chunk
            except ValueError as exc:  # llama.cpp: prompt longer than the context window
                raise AppError(400, "generation_failed", str(exc)) from exc
            finally:
                self._last_used = time.monotonic()
