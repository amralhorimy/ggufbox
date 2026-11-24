from fastapi import APIRouter, Depends

from ..container import Container
from ..core.resources import memory_snapshot
from .deps import get_container

public = APIRouter(tags=["system"])
router = APIRouter(tags=["system"])


@public.get("/health")
async def health():
    return {"status": "ok"}


@router.get("/system")
async def system(c: Container = Depends(get_container)):
    import os
    return {"memory": memory_snapshot(), "cpu_count": os.cpu_count(), "engine": c.engine.name,
            "auth_required": bool(c.settings.api_key), "model": c.manager.status()}
