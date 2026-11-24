import mimetypes
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, UploadFile
from fastapi.responses import FileResponse

from ..container import Container
from ..core.errors import AppError
from .deps import get_container

router = APIRouter(prefix="/uploads", tags=["uploads"])
IMAGE_TYPES = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp",
               ".gif": "image/gif"}
TEXT_EXT = {".txt", ".md", ".csv", ".json", ".py", ".js", ".ts", ".html", ".css", ".xml", ".yaml", ".yml",
            ".log", ".sql", ".ini", ".toml", ".java", ".c", ".cpp", ".go", ".rs", ".sh", ".tex"}


@router.post("", status_code=201, summary="Upload an image or a text/PDF file to attach to a message")
async def upload(file: UploadFile, c: Container = Depends(get_container)):
    ext = Path(file.filename or "").suffix.lower()
    if ext in IMAGE_TYPES:
        kind, mime = "image", IMAGE_TYPES[ext]
    elif ext == ".pdf":
        kind, mime = "pdf", "application/pdf"
    elif ext in TEXT_EXT:
        kind, mime = "text", "text/plain"
    else:
        raise AppError(415, "unsupported_file", "Supported: images (png, jpg, webp, gif), PDF, and text/code files.")
    limit = c.settings.max_upload_mb * 1024 * 1024
    dest = c.settings.uploads_dir / f"{uuid.uuid4().hex}{ext}"
    size = 0
    with dest.open("wb") as out:
        while chunk := await file.read(1024 * 1024):
            size += len(chunk)
            if size > limit:
                out.close()
                dest.unlink(missing_ok=True)
                raise AppError(413, "file_too_large", f"Files are limited to {c.settings.max_upload_mb} MB.")
            out.write(chunk)
    row = await c.uploads.create(Path(file.filename).name, mime, kind, size, str(dest))
    return {k: row[k] for k in ("id", "filename", "kind", "size")}


@router.get("/{upload_id}")
async def download(upload_id: str, c: Container = Depends(get_container)):
    row = await c.uploads.get(upload_id)
    if not row:
        raise AppError(404, "upload_not_found", "Upload not found.")
    return FileResponse(row["path"], media_type=row["mime"] or mimetypes.guess_type(row["path"])[0])
