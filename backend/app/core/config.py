from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    database_url: str

    auth_secret: str

    admin_email: str = "admin@peblo.local"
    admin_password: str = "change-me-admin"

    editor_email: str = "editor@peblo.local"
    editor_password: str = "change-me-editor"

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()