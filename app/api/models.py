from fastapi import APIRouter, Depends, Query

from ..container import Container
from ..schemas import LoadParams, LoadRequest
from .deps import get_container

router = APIRouter(prefix="/models", tags=["models"])


@router.get("", summary="List GGUF files found in the models folder")
async def list_models(c: Container = Depends(get_container)):
    return [m.as_dict() for m in c.manager.scan()]


@router.get("/status", summary="Which model is loaded, and with what settings")
async def status(c: Container = Depends(get_container)):
    return c.manager.status()


@router.get("/estimate", summary="Estimate the RAM a load would need, before loading")
async def estimate(filename: str, n_ctx: int = Query(4096, ge=256), n_gpu_layers: int = Query(0, ge=-1),
                   c: Container = Depends(get_container)):
    return c.manager.estimate(filename, n_ctx, n_gpu_layers)


@router.post("/load", summary="Load a model into RAM (replaces the current one)")
async def load(body: LoadRequest, c: Container = Depends(get_container)):
    LoadParams.model_validate(body.overrides)  # fail fast with a clear 422
    await c.manager.load_with_preset(body.filename, body.preset_id, body.overrides, body.force)
    return c.manager.status()


@router.post("/unload", summary="Free the RAM used by the current model")
async def unload(c: Container = Depends(get_container)):
    await c.manager.unload()
    return c.manager.status()
