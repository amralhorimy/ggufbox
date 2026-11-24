"""Chat orchestration. Chats are stored model-neutral; the model's template is applied only at call time,
which is why you can switch models in the middle of a conversation."""
import asyncio
import json
import logging
from contextlib import aclosing
from dataclasses import dataclass
from typing import AsyncIterator

from ..config import Settings
from ..core.errors import AppError
from ..db.repositories import ChatRepo, UploadRepo
from ..engine import GenParams
from ..schemas import PresetOptions, SendMessage
from .completion import CompletionService
from .model_manager import ModelManager
from .prompting import (append_to_last_user, extract_text, fit_context, image_data_uri)

log = logging.getLogger("ggufbox")
DEFAULT_TITLE = "New chat"
SUMMARY_SYSTEM = ("You summarise conversations. Reply in the language of the conversation with: a 2-3 sentence "
                  "overview, then bullet points for key facts, decisions and open questions. Be concise.")


@dataclass
class Turn:
    """A prepared (validated, persisted-user-side) request, ready to stream."""
    chat: dict
    user_message: dict | None
    messages: list[dict]
    params: GenParams
    thinking: bool
    prefilled: bool
    truncated: int
    model: str


class ChatService:
    def __init__(self, settings: Settings, chats: ChatRepo, uploads: UploadRepo, manager: ModelManager,
                 completion: CompletionService):
        self.settings, self.chats, self.uploads = settings, chats, uploads
        self.manager, self.completion = manager, completion

    async def require_chat(self, chat_id: str) -> dict:
        chat = await self.chats.get(chat_id)
        if not chat:
            raise AppError(404, "chat_not_found", "Chat not found.")
        return chat

    async def _to_engine(self, msg: dict, vision: bool) -> dict:
        if msg["role"] == "assistant" or not msg["attachments"]:
            return {"role": msg["role"], "content": msg["content"]}
        text, images = msg["content"], []
        for uid in msg["attachments"]:
            up = await self.uploads.get(uid)
            if not up:
                text += f"\n\n[Attachment {uid} is no longer available]"
            elif up["kind"] == "image":
                if vision:
                    images.append(image_data_uri(up["path"], up["mime"]))
                else:
                    text += f"\n\n[Image '{up['filename']}' omitted: the loaded model cannot see images]"
            else:
                body = await asyncio.to_thread(extract_text, up["path"], up["kind"], self.settings.max_file_chars)
                text += f"\n\n[Attached file: {up['filename']}]\n```\n{body}\n```"
        if not images:
            return {"role": msg["role"], "content": text}
        # SmolVLM's documented message format places the image before its question text.
        parts = [{"type": "image_url", "image_url": {"url": u}} for u in images]
        parts.append({"type": "text", "text": text})
        return {"role": msg["role"], "content": parts}

    async def prepare(self, chat_id: str, req: SendMessage) -> Turn:
        chat = await self.require_chat(chat_id)
        await self.manager.restore()
        loaded = self.manager.current
        if loaded is None:
            raise AppError(409, "no_model_loaded", "No model is loaded. Load one from the Models page first.")
        history = await self.chats.messages(chat_id)
        user_message = None
        if req.regenerate:
            while history and history[-1]["role"] == "assistant":
                await self.chats.delete_message(history.pop()["id"])
            if not history:
                raise AppError(400, "nothing_to_regenerate", "There is no user message to answer.")
        else:
            if not req.content.strip() and not req.attachments:
                raise AppError(400, "empty_message", "Write a message or attach a file.")
            for uid in req.attachments:
                up = await self.uploads.get(uid)
                if not up:
                    raise AppError(404, "attachment_not_found", f"Attachment {uid} not found.")
                if up["kind"] == "image" and loaded and not loaded.vision:
                    raise AppError(400, "vision_unsupported",
                                   "The loaded model cannot read images. Load a vision model (one with an mmproj file).")
            user_message = await self.chats.add_message(chat_id, "user", req.content, attachments=req.attachments)
            history.append(user_message)

        vision = bool(loaded and loaded.vision)
        options = PresetOptions.model_validate(loaded.options if loaded else {})
        params = self.completion.build_params(req.gen)
        n_ctx = loaded.params["n_ctx"] if loaded else 4096
        engine_history = [await self._to_engine(m, vision) for m in history]
        system = {"role": "system", "content": chat["system_prompt"]} if chat["system_prompt"].strip() else None
        budget = n_ctx - params.max_tokens - 64
        if budget < 256:
            raise AppError(400, "max_tokens_too_large", "max_tokens leaves no room for the prompt in this context.")
        messages, dropped = fit_context(system, engine_history, self.manager.count_tokens, budget)
        if not req.thinking:
            append_to_last_user(messages, options.think_off_directive)

        if chat["title"] == DEFAULT_TITLE and not req.regenerate and req.content.strip():
            await self.chats.update(chat_id, title=req.content.strip().replace("\n", " ")[:48])
            chat = await self.chats.get(chat_id)
        return Turn(chat, user_message, messages, params, req.thinking, options.think_prefilled, dropped,
                    loaded.filename if loaded else "")

    async def events(self, turn: Turn) -> AsyncIterator[tuple[str, dict]]:
        """Yields (event, data): meta, token*, reasoning*, error?, done. Persists the answer even if the client leaves."""
        model_name = self.manager.current.filename if self.manager.current else turn.model
        yield "meta", {"chat_id": turn.chat["id"], "title": turn.chat["title"], "model": model_name,
                       "user_message": turn.user_message, "truncated_messages": turn.truncated}
        content, reasoning, info, error = [], [], {"finish_reason": "stop", "completion_tokens": 0, "seconds": 0}, None
        try:
            async with aclosing(self.completion.stream(turn.messages, turn.params, prefilled=turn.prefilled)) as stream:
                async for kind, value in stream:
                    if kind == "content":
                        content.append(value)
                        yield "token", {"text": value}
                    elif kind == "reasoning":
                        if turn.thinking:
                            reasoning.append(value)
                            yield "reasoning", {"text": value}
                    else:
                        info = value
        except asyncio.CancelledError:
            info["finish_reason"] = "cancelled"
            raise
        except AppError as exc:
            error, info["finish_reason"] = {"code": exc.code, "message": exc.message}, "error"
            yield "error", error
        except Exception as exc:
            log.exception("generation failed")
            error, info["finish_reason"] = {"code": "generation_failed", "message": str(exc)}, "error"
            yield "error", error
        finally:
            text = "".join(content).strip()
            saved = None
            if text or reasoning:
                usage = {**info, "tokens_per_second": round(info["completion_tokens"] / info["seconds"], 1)
                         if info.get("seconds") else None}
                saved = await asyncio.shield(self.chats.add_message(
                    turn.chat["id"], "assistant", text, reasoning="".join(reasoning).strip() or None,
                    model=model_name, usage=usage))
        yield "done", {"message": saved, "usage": saved["usage"] if saved else info}

    async def summarize(self, chat_id: str) -> str:
        chat = await self.require_chat(chat_id)
        loaded = self.manager.current
        history = await self.chats.messages(chat_id)
        if not history:
            raise AppError(400, "empty_chat", "There is nothing to summarise yet.")
        params = self.completion.build_params({"temperature": 0.3, "max_tokens": 400})
        n_ctx = loaded.params["n_ctx"] if loaded else 4096
        budget = n_ctx - params.max_tokens - 200
        lines, used = [], 0
        for m in reversed(history):
            line = f"{m['role'].upper()}: {m['content']}"
            cost = self.manager.count_tokens(line)
            if lines and used + cost > budget:
                break
            lines.append(line[: budget * 3] if not lines else line)
            used += cost
        transcript = "\n\n".join(reversed(lines))
        result = await self.completion.collect(
            [{"role": "system", "content": SUMMARY_SYSTEM},
             {"role": "user", "content": f"Summarise this conversation:\n\n{transcript}"}], params)
        summary = result["content"]
        if not summary:
            raise AppError(502, "empty_summary", "The model returned an empty summary. Try again.")
        await self.chats.update(chat["id"], summary=summary)
        return summary

    async def export(self, chat_id: str, fmt: str) -> tuple[str, str, str]:
        """Returns (body, media_type, extension)."""
        chat = await self.require_chat(chat_id)
        messages = await self.chats.messages(chat_id)
        if fmt == "json":
            return json.dumps({"chat": chat, "messages": messages}, ensure_ascii=False, indent=2), "application/json", "json"
        if fmt == "txt":
            body = "\n\n".join(f"{m['role'].capitalize()}: {m['content']}" for m in messages)
            return f"{chat['title']}\n\n{body}\n", "text/plain", "txt"
        parts = [f"# {chat['title']}\n"]
        if chat["summary"]:
            parts.append(f"> **Summary**\n>\n> " + chat["summary"].replace("\n", "\n> ") + "\n")
        for m in messages:
            parts.append(f"### {'You' if m['role'] == 'user' else 'Assistant'}\n")
            if m["reasoning"]:
                parts.append(f"<details><summary>Reasoning</summary>\n\n{m['reasoning']}\n\n</details>\n")
            parts.append(m["content"] + "\n")
        return "\n".join(parts), "text/markdown", "md"
