from fastapi import Request
from fastapi.responses import JSONResponse


class AppError(Exception):
    """A predictable failure that maps to a clean JSON error: {"error": {"code", "message"}}."""

    def __init__(self, status: int, code: str, message: str, details: dict | None = None):
        super().__init__(message)
        self.status, self.code, self.message, self.details = status, code, message, details


async def app_error_handler(_: Request, exc: AppError) -> JSONResponse:
    body: dict = {"error": {"code": exc.code, "message": exc.message}}
    if exc.details:
        body["error"]["details"] = exc.details
    return JSONResponse(body, status_code=exc.status)
