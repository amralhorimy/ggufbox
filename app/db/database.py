from pathlib import Path

import aiosqlite

SCHEMA = """
CREATE TABLE IF NOT EXISTS chats(
  id TEXT PRIMARY KEY, title TEXT NOT NULL, system_prompt TEXT NOT NULL DEFAULT '',
  summary TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS messages(
  id TEXT PRIMARY KEY, chat_id TEXT NOT NULL REFERENCES chats(id) ON DELETE CASCADE,
  role TEXT NOT NULL, content TEXT NOT NULL, reasoning TEXT, model TEXT,
  attachments TEXT NOT NULL DEFAULT '[]', usage TEXT, created_at TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS idx_messages_chat ON messages(chat_id);
CREATE TABLE IF NOT EXISTS presets(
  id TEXT PRIMARY KEY, name TEXT UNIQUE NOT NULL, model_filename TEXT,
  load_params TEXT NOT NULL, gen_params TEXT NOT NULL, options TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS virtual_apis(
  slug TEXT PRIMARY KEY, name TEXT NOT NULL, description TEXT NOT NULL DEFAULT '',
  system_prompt TEXT NOT NULL DEFAULT '', input_template TEXT NOT NULL DEFAULT '',
  preset_id TEXT, model_filename TEXT, gen_params TEXT NOT NULL DEFAULT '{}',
  output_schema TEXT, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS uploads(
  id TEXT PRIMARY KEY, filename TEXT NOT NULL, mime TEXT NOT NULL, kind TEXT NOT NULL,
  size INTEGER NOT NULL, path TEXT NOT NULL, created_at TEXT NOT NULL);
"""


class Database:
    """One shared SQLite connection (aiosqlite serialises access on its own thread)."""

    def __init__(self, path: Path):
        self.path = path
        self.conn: aiosqlite.Connection | None = None

    async def connect(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = await aiosqlite.connect(self.path)
        self.conn.row_factory = aiosqlite.Row
        await self.conn.execute("PRAGMA foreign_keys=ON")
        await self.conn.execute("PRAGMA journal_mode=WAL")
        await self.conn.executescript(SCHEMA)
        await self.conn.commit()

    async def close(self) -> None:
        if self.conn:
            await self.conn.close()

    async def one(self, sql: str, args: tuple = ()) -> dict | None:
        cur = await self.conn.execute(sql, args)
        row = await cur.fetchone()
        await cur.close()
        return dict(row) if row else None

    async def all(self, sql: str, args: tuple = ()) -> list[dict]:
        cur = await self.conn.execute(sql, args)
        rows = await cur.fetchall()
        await cur.close()
        return [dict(r) for r in rows]

    async def run(self, sql: str, args: tuple = ()) -> None:
        await self.conn.execute(sql, args)
        await self.conn.commit()
