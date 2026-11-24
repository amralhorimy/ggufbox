import hmac

from fastapi import Request

from .errors import AppError


async def require_api_key(request: Request) -> None:
    """Optional shared-secret auth. Disabled unless GGUFBOX_API_KEY is set."""
    expected = request.app.state.container.settings.api_key
    if not expected:
        return
    supplied = request.headers.get("x-api-key", "")
    auth = request.headers.get("authorization", "")
    if auth.lower().startswith("bearer "):
        supplied = auth[7:].strip()
    supplied = supplied or request.query_params.get("key", "")
    if not hmac.compare_digest(supplied.encode(), expected.encode()):
        raise AppError(401, "unauthorized", "Missing or invalid API key.")
