import json
from urllib.parse import quote

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse, Response, StreamingResponse

from ..container import Container
from ..schemas import ChatCreate, ChatUpdate, SendMessage
from ..services.chat_service import DEFAULT_TITLE
from .deps import get_container

router = APIRouter(prefix="/chats", tags=["chats"])


def sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


@router.get("")
async def list_chats(c: Container = Depends(get_container)):
    return await c.chats.list()


@router.post("", status_code=201)
async def create_chat(body: ChatCreate, c: Container = Depends(get_container)):
    return await c.chats.create(body.title or DEFAULT_TITLE, body.system_prompt)


@router.get("/{chat_id}")
async def get_chat(chat_id: str, c: Container = Depends(get_container)):
    chat = await c.chat_service.require_chat(chat_id)
    return {**chat, "messages": await c.chats.messages(chat_id)}


@router.patch("/{chat_id}")
async def update_chat(chat_id: str, body: ChatUpdate, c: Container = Depends(get_container)):
    await c.chat_service.require_chat(chat_id)
    await c.chats.update(chat_id, title=body.title, system_prompt=body.system_prompt)
    return await c.chats.get(chat_id)


@router.delete("/{chat_id}", status_code=204)
async def delete_chat(chat_id: str, c: Container = Depends(get_container)):
    await c.chats.delete(chat_id)


@router.post("/{chat_id}/messages",
             summary="Send a message. Streams Server-Sent Events by default (meta, token, reasoning, error, done).")
async def send_message(chat_id: str, body: SendMessage, c: Container = Depends(get_container)):
    turn = await c.chat_service.prepare(chat_id, body)  # validation errors surface as normal HTTP errors
    events = c.chat_service.events(turn)
    if body.stream:
        async def gen():
            try:
                async for event, data in events:
                    yield sse(event, data)
            finally:
                await events.aclose()
        return StreamingResponse(gen(), media_type="text/event-stream",
                                 headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})
    final, error = {}, None
    async for event, data in events:
        if event == "error":
            error = data
        elif event == "done":
            final = data
    if error:
        return JSONResponse({"error": error}, status_code=502)
    return final


@router.post("/{chat_id}/summarize", summary="Summarise the chat with the loaded model and store the summary")
async def summarize(chat_id: str, c: Container = Depends(get_container)):
    return {"summary": await c.chat_service.summarize(chat_id)}


@router.get("/{chat_id}/export", summary="Download the chat as Markdown, JSON or plain text")
async def export(chat_id: str, format: str = Query("md", pattern="^(md|json|txt)$"),
                 c: Container = Depends(get_container)):
    body, media, ext = await c.chat_service.export(chat_id, format)
    chat = await c.chats.get(chat_id)
    name = quote(f"{chat['title'][:40] or 'chat'}.{ext}")
    return Response(body, media_type=f"{media}; charset=utf-8",
                    headers={"Content-Disposition": f"attachment; filename*=UTF-8''{name}"})
