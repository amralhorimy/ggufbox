"""OpenAI-compatible surface so existing SDKs and tools work unchanged: GET /v1/models, POST /v1/chat/completions."""
import json
import time
import uuid

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from ..container import Container
from ..core.errors import AppError
from ..schemas import ChatCompletionRequest
from .deps import get_container

router = APIRouter(prefix="/v1", tags=["openai-compatible"])


@router.get("/models")
async def models(c: Container = Depends(get_container)):
    loaded = c.manager.current.filename if c.manager.current else None
    return {"object": "list", "data": [
        {"id": m.filename, "object": "model", "created": 0, "owned_by": "local", "loaded": m.filename == loaded}
        for m in c.manager.scan()]}


def _schema_of(fmt: dict | None) -> dict | None:
    if not fmt:
        return None
    if fmt.get("type") == "json_schema":
        return (fmt.get("json_schema") or {}).get("schema")
    if fmt.get("type") == "json_object":
        return fmt.get("schema") or {"type": "object"}
    return None


@router.post("/chat/completions")
async def chat_completions(body: ChatCompletionRequest, c: Container = Depends(get_container)):
    wanted = body.model if body.model and body.model not in {"default", "current", "local"} else None
    await c.manager.ensure(wanted)
    await c.manager.restore()
    loaded = c.manager.current
    if loaded is None:
        raise AppError(409, "no_model_loaded", "No model is loaded.")
    has_image = any(isinstance(m.get("content"), list) and any(p.get("type") == "image_url" for p in m["content"])
                    for m in body.messages)
    if has_image and not loaded.vision:
        raise AppError(400, "vision_unsupported", "The loaded model cannot read images.")
    stop = [body.stop] if isinstance(body.stop, str) else body.stop
    overrides = {"temperature": body.temperature, "top_p": body.top_p, "max_tokens": body.max_tokens,
                 "seed": body.seed, "stop": stop}
    params = c.completion.build_params(overrides, _schema_of(body.response_format))
    prefilled = bool(loaded.options.get("think_prefilled"))
    cid, created = f"chatcmpl-{uuid.uuid4().hex[:20]}", int(time.time())

    def chunk(delta: dict, finish: str | None = None, usage: dict | None = None) -> str:
        obj = {"id": cid, "object": "chat.completion.chunk", "created": created, "model": loaded.filename,
               "choices": [{"index": 0, "delta": delta, "finish_reason": finish}]}
        if usage:
            obj["usage"] = usage
        return f"data: {json.dumps(obj, ensure_ascii=False)}\n\n"

    if body.stream:
        async def gen():
            events = c.completion.stream(body.messages, params, prefilled=prefilled)
            try:
                yield chunk({"role": "assistant", "content": ""})
                async for kind, value in events:
                    if kind == "content":
                        yield chunk({"content": value})
                    elif kind == "reasoning":
                        yield chunk({"reasoning_content": value})
                    else:
                        n = value["completion_tokens"]
                        yield chunk({}, value["finish_reason"], {"completion_tokens": n})
                yield "data: [DONE]\n\n"
            except AppError as exc:
                yield f"data: {json.dumps({'error': {'code': exc.code, 'message': exc.message}})}\n\n"
            finally:
                await events.aclose()

        return StreamingResponse(gen(), media_type="text/event-stream",
                                 headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

    result = await c.completion.collect(body.messages, params, prefilled=prefilled)
    message = {"role": "assistant", "content": result["content"]}
    if result["reasoning"]:
        message["reasoning_content"] = result["reasoning"]
    return {"id": cid, "object": "chat.completion", "created": created, "model": loaded.filename,
            "choices": [{"index": 0, "message": message, "finish_reason": result["finish_reason"]}],
            "usage": {"completion_tokens": result["completion_tokens"]}}
