import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI
from fastapi.staticfiles import StaticFiles

from .api import chats, models, openai, presets, system, uploads, virtual
from .config import get_settings
from .container import build_container
from .core.errors import AppError, app_error_handler
from .core.security import require_api_key

STATIC = Path(__file__).parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    container = build_container(get_settings())
    app.state.container = container
    await container.db.connect()
    await container.presets.seed_defaults()
    watchdog = asyncio.create_task(container.manager.idle_watchdog())
    yield
    watchdog.cancel()
    await container.manager.unload()
    await container.db.close()


def create_app() -> FastAPI:
    app = FastAPI(
        title="GGUFBox",
        version="0.1.0",
        description="Run any local GGUF model with a light control panel, a clean REST API, "
                    "an OpenAI-compatible endpoint and custom virtual APIs.",
        lifespan=lifespan,
    )
    app.add_exception_handler(AppError, app_error_handler)
    app.include_router(system.public, prefix="/api")
    secured = [Depends(require_api_key)]
    for router in (system.router, models.router, presets.router, chats.router, uploads.router, virtual.router):
        app.include_router(router, prefix="/api", dependencies=secured)
    app.include_router(openai.router, dependencies=secured)
    app.mount("/", StaticFiles(directory=STATIC, html=True), name="ui")
    return app


app = create_app()
