import json
import sqlite3

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from ..container import Container
from ..core.errors import AppError
from ..schemas import VirtualApiIn, VirtualRun
from .chats import sse
from .deps import get_container

router = APIRouter(tags=["virtual apis"])


@router.get("/virtual-apis")
async def list_virtual(c: Container = Depends(get_container)):
    return await c.virtual_apis.list()


@router.post("/virtual-apis", status_code=201, summary="Create an endpoint from a prompt, a model and (optionally) a JSON schema")
async def create_virtual(body: VirtualApiIn, c: Container = Depends(get_container)):
    try:
        return await c.virtual_apis.save(body.slug, body.model_dump(exclude={"slug"}), create=True)
    except sqlite3.IntegrityError:
        raise AppError(409, "slug_exists", f"An API named '{body.slug}' already exists.")


@router.put("/virtual-apis/{slug}")
async def update_virtual(slug: str, body: VirtualApiIn, c: Container = Depends(get_container)):
    if not await c.virtual_apis.get(slug):
        raise AppError(404, "virtual_api_not_found", f"No virtual API named '{slug}'.")
    return await c.virtual_apis.save(slug, body.model_dump(exclude={"slug"}), create=False)


@router.delete("/virtual-apis/{slug}", status_code=204)
async def delete_virtual(slug: str, c: Container = Depends(get_container)):
    await c.virtual_apis.delete(slug)


@router.post("/v/{slug}", summary="Call a virtual API. Returns JSON, or SSE when stream=true.")
async def call_virtual(slug: str, body: VirtualRun, c: Container = Depends(get_container)):
    if not body.stream:
        return await c.virtual_service.run(slug, body)
    events, show_reasoning = await c.virtual_service.stream(slug, body)

    async def gen():
        try:
            async for kind, value in events:
                if kind == "content":
                    yield sse("token", {"text": value})
                elif kind == "reasoning" and show_reasoning:
                    yield sse("reasoning", {"text": value})
                elif kind == "finish":
                    yield sse("done", value)
        except AppError as exc:
            yield sse("error", {"code": exc.code, "message": exc.message})
        finally:
            await events.aclose()

    return StreamingResponse(gen(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})
