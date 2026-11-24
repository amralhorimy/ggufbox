"""Pure helpers that turn stored chats/templates into engine input."""
import base64
import re
from pathlib import Path
from typing import Callable

from ..core.errors import AppError

IMAGE_TOKEN_COST = 700  # rough cost of one image in context, used only for budgeting
_PLACEHOLDER = re.compile(r"\{\{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\}\}")


def render_template(template: str, input_text: str, variables: dict[str, str]) -> str:
    if not template:
        return input_text
    values = {**variables, "input": input_text}
    missing = sorted({m for m in _PLACEHOLDER.findall(template) if m not in values})
    if missing:
        raise AppError(422, "missing_variables", f"Missing template variables: {', '.join(missing)}")
    return _PLACEHOLDER.sub(lambda m: values[m.group(1)], template)


def extract_text(path: str, kind: str, limit: int) -> str:
    p = Path(path)
    if kind == "pdf":
        try:
            from pypdf import PdfReader
            text = "\n".join((page.extract_text() or "") for page in PdfReader(str(p)).pages)
        except Exception as exc:
            raise AppError(422, "pdf_unreadable", f"Could not read the PDF: {exc}") from exc
    else:
        text = p.read_bytes().decode("utf-8", errors="replace")
    if len(text) > limit:
        text = text[:limit] + f"\n[... truncated, {len(text) - limit} more characters]"
    return text


def image_data_uri(path: str, mime: str) -> str:
    return f"data:{mime};base64," + base64.b64encode(Path(path).read_bytes()).decode()


def message_tokens(message: dict, count: Callable[[str], int]) -> int:
    content = message["content"]
    if isinstance(content, str):
        return count(content) + 8
    return 8 + sum(count(p["text"]) if p.get("type") == "text" else IMAGE_TOKEN_COST for p in content)


def fit_context(system: dict | None, history: list[dict], count: Callable[[str], int],
                budget: int) -> tuple[list[dict], int]:
    """Keep the system prompt and the newest messages that fit `budget` tokens. Returns (messages, dropped)."""
    used = message_tokens(system, count) if system else 0
    kept: list[dict] = []
    for msg in reversed(history):
        cost = message_tokens(msg, count)
        if kept and used + cost > budget:
            break
        if not kept and used + cost > budget:
            raise AppError(400, "message_too_long",
                           "This message does not fit in the model's context. Shorten it or load the model with a larger n_ctx.")
        kept.append(msg)
        used += cost
    kept.reverse()
    while kept and kept[0]["role"] != "user":  # templates expect the first turn to be the user's
        kept.pop(0)
    return ([system] if system else []) + kept, len(history) - len(kept)


def append_to_last_user(messages: list[dict], suffix: str) -> None:
    if not suffix:
        return
    for msg in reversed(messages):
        if msg["role"] == "user":
            if isinstance(msg["content"], str):
                msg["content"] += f"\n{suffix}"
            else:
                for part in msg["content"]:
                    if part.get("type") == "text":
                        part["text"] += f"\n{suffix}"
                        break
            return
