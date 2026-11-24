from dataclasses import dataclass

from .config import Settings
from .db.database import Database
from .db.repositories import ChatRepo, PresetRepo, UploadRepo, VirtualApiRepo
from .engine import Engine, create_engine
from .services.chat_service import ChatService
from .services.completion import CompletionService
from .services.model_manager import ModelManager
from .services.virtual_api_service import VirtualApiService


@dataclass
class Container:
    settings: Settings
    db: Database
    engine: Engine
    chats: ChatRepo
    presets: PresetRepo
    uploads: UploadRepo
    virtual_apis: VirtualApiRepo
    manager: ModelManager
    completion: CompletionService
    chat_service: ChatService
    virtual_service: VirtualApiService


def build_container(settings: Settings) -> Container:
    settings.models_dir.mkdir(parents=True, exist_ok=True)
    settings.uploads_dir.mkdir(parents=True, exist_ok=True)
    db = Database(settings.db_path)
    chats, presets, uploads, vapis = ChatRepo(db), PresetRepo(db), UploadRepo(db), VirtualApiRepo(db)
    engine = create_engine(settings.engine)
    manager = ModelManager(settings, engine, presets)
    completion = CompletionService(manager)
    return Container(settings, db, engine, chats, presets, uploads, vapis, manager, completion,
                     ChatService(settings, chats, uploads, manager, completion),
                     VirtualApiService(vapis, manager, completion))
