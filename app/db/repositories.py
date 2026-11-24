"""Plain data access. No business rules here, just SQL <-> dicts."""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone

from .database import Database


def new_id() -> str:
    return uuid.uuid4().hex[:12]


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _dump(value) -> str:
    return json.dumps(value, ensure_ascii=False)


class ChatRepo:
    def __init__(self, db: Database):
        self.db = db

    async def create(self, title: str, system_prompt: str = "") -> dict:
        cid, ts = new_id(), now()
        await self.db.run("INSERT INTO chats(id,title,system_prompt,created_at,updated_at) VALUES(?,?,?,?,?)",
                          (cid, title, system_prompt, ts, ts))
        return await self.get(cid)

    async def list(self) -> list[dict]:
        return await self.db.all(
            "SELECT c.id,c.title,c.updated_at,(SELECT COUNT(*) FROM messages m WHERE m.chat_id=c.id) AS message_count "
            "FROM chats c ORDER BY c.updated_at DESC")

    async def get(self, chat_id: str) -> dict | None:
        return await self.db.one("SELECT * FROM chats WHERE id=?", (chat_id,))

    async def update(self, chat_id: str, **fields) -> None:
        allowed = {k: v for k, v in fields.items() if k in {"title", "system_prompt", "summary"} and v is not None}
        if allowed:
            sets = ",".join(f"{k}=?" for k in allowed)
            await self.db.run(f"UPDATE chats SET {sets}, updated_at=? WHERE id=?", (*allowed.values(), now(), chat_id))

    async def touch(self, chat_id: str) -> None:
        await self.db.run("UPDATE chats SET updated_at=? WHERE id=?", (now(), chat_id))

    async def delete(self, chat_id: str) -> None:
        await self.db.run("DELETE FROM chats WHERE id=?", (chat_id,))

    @staticmethod
    def _decode(row: dict) -> dict:
        row["attachments"] = json.loads(row["attachments"] or "[]")
        row["usage"] = json.loads(row["usage"]) if row["usage"] else None
        return row

    async def messages(self, chat_id: str) -> list[dict]:
        rows = await self.db.all("SELECT * FROM messages WHERE chat_id=? ORDER BY rowid", (chat_id,))
        return [self._decode(r) for r in rows]

    async def add_message(self, chat_id: str, role: str, content: str, *, reasoning: str | None = None,
                          model: str | None = None, attachments: list[str] | None = None,
                          usage: dict | None = None) -> dict:
        mid = new_id()
        await self.db.run(
            "INSERT INTO messages(id,chat_id,role,content,reasoning,model,attachments,usage,created_at) "
            "VALUES(?,?,?,?,?,?,?,?,?)",
            (mid, chat_id, role, content, reasoning, model, _dump(attachments or []),
             _dump(usage) if usage else None, now()))
        await self.touch(chat_id)
        return self._decode(await self.db.one("SELECT * FROM messages WHERE id=?", (mid,)))

    async def delete_message(self, message_id: str) -> None:
        await self.db.run("DELETE FROM messages WHERE id=?", (message_id,))


class PresetRepo:
    DEFAULTS = [
        ("Balanced", {"n_ctx": 4096}, {}, {}),
        ("Low RAM", {"n_ctx": 2048, "n_batch": 256, "use_mmap": True}, {"max_tokens": 512}, {}),
        ("Long context", {"n_ctx": 16384, "flash_attn": True}, {"max_tokens": 2048}, {}),
    ]

    def __init__(self, db: Database):
        self.db = db

    @staticmethod
    def _decode(row: dict | None) -> dict | None:
        if row:
            for key in ("load_params", "gen_params", "options"):
                row[key] = json.loads(row[key] or "{}")
        return row

    async def seed_defaults(self) -> None:
        if (await self.db.one("SELECT COUNT(*) AS n FROM presets"))["n"] == 0:
            for name, load, gen, opts in self.DEFAULTS:
                await self.create(name, None, load, gen, opts)

    async def create(self, name: str, model_filename: str | None, load_params: dict, gen_params: dict,
                     options: dict) -> dict:
        pid = new_id()
        await self.db.run("INSERT INTO presets VALUES(?,?,?,?,?,?,?)",
                          (pid, name, model_filename, _dump(load_params), _dump(gen_params), _dump(options), now()))
        return await self.get(pid)

    async def list(self) -> list[dict]:
        return [self._decode(r) for r in await self.db.all("SELECT * FROM presets ORDER BY name")]

    async def get(self, preset_id: str) -> dict | None:
        return self._decode(await self.db.one("SELECT * FROM presets WHERE id=?", (preset_id,)))

    async def for_model(self, filename: str) -> dict | None:
        return self._decode(await self.db.one("SELECT * FROM presets WHERE model_filename=? ORDER BY name LIMIT 1",
                                              (filename,)))

    async def update(self, preset_id: str, name: str, model_filename: str | None, load_params: dict,
                     gen_params: dict, options: dict) -> dict | None:
        await self.db.run("UPDATE presets SET name=?,model_filename=?,load_params=?,gen_params=?,options=? WHERE id=?",
                          (name, model_filename, _dump(load_params), _dump(gen_params), _dump(options), preset_id))
        return await self.get(preset_id)

    async def delete(self, preset_id: str) -> None:
        await self.db.run("DELETE FROM presets WHERE id=?", (preset_id,))


class VirtualApiRepo:
    def __init__(self, db: Database):
        self.db = db

    @staticmethod
    def _decode(row: dict | None) -> dict | None:
        if row:
            row["gen_params"] = json.loads(row["gen_params"] or "{}")
            row["output_schema"] = json.loads(row["output_schema"]) if row["output_schema"] else None
        return row

    async def list(self) -> list[dict]:
        return [self._decode(r) for r in await self.db.all("SELECT * FROM virtual_apis ORDER BY name")]

    async def get(self, slug: str) -> dict | None:
        return self._decode(await self.db.one("SELECT * FROM virtual_apis WHERE slug=?", (slug,)))

    async def save(self, slug: str, data: dict, *, create: bool) -> dict:
        values = (data["name"], data["description"], data["system_prompt"], data["input_template"],
                  data["preset_id"], data["model_filename"], _dump(data["gen_params"]),
                  _dump(data["output_schema"]) if data["output_schema"] else None)
        if create:
            await self.db.run("INSERT INTO virtual_apis VALUES(?,?,?,?,?,?,?,?,?,?)", (slug, *values, now()))
        else:
            await self.db.run("UPDATE virtual_apis SET name=?,description=?,system_prompt=?,input_template=?,"
                              "preset_id=?,model_filename=?,gen_params=?,output_schema=? WHERE slug=?",
                              (*values, slug))
        return await self.get(slug)

    async def delete(self, slug: str) -> None:
        await self.db.run("DELETE FROM virtual_apis WHERE slug=?", (slug,))


class UploadRepo:
    def __init__(self, db: Database):
        self.db = db

    async def create(self, filename: str, mime: str, kind: str, size: int, path: str) -> dict:
        uid = new_id()
        await self.db.run("INSERT INTO uploads VALUES(?,?,?,?,?,?,?)", (uid, filename, mime, kind, size, path, now()))
        return await self.get(uid)

    async def get(self, upload_id: str) -> dict | None:
        return await self.db.one("SELECT * FROM uploads WHERE id=?", (upload_id,))

    async def delete(self, upload_id: str) -> None:
        await self.db.run("DELETE FROM uploads WHERE id=?", (upload_id,))
