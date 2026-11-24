from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="GGUFBOX_", env_file=".env", extra="ignore")

    engine: str = "llama_cpp"
    models_dir: Path = Path("./models")
    data_dir: Path = Path("./data")
    api_key: str | None = None
    ram_budget_fraction: float = 0.85
    idle_unload_seconds: int = 0
    auto_load: bool = True
    max_upload_mb: int = 20
    max_file_chars: int = 24000

    @property
    def db_path(self) -> Path:
        return self.data_dir / "ggufbox.sqlite3"

    @property
    def uploads_dir(self) -> Path:
        return self.data_dir / "uploads"


@lru_cache
def get_settings() -> Settings:
    return Settings()
