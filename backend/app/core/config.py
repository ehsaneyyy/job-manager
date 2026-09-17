from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    api_key: str = "change-me-to-a-long-random-string"
    llm_provider: str = "openrouter"
    llm_base_url: str = "https://openrouter.ai/api/v1"
    llm_api_key: str = ""
    llm_model: str = "meta-llama/llama-3.3-70b-instruct:free"
    database_url: str = "sqlite+aiosqlite:///./data/jobmanager.db"
    data_dir: Path = Path("./data")
    browser_headless: bool = True
    browser_profile_dir: Path = Path("./data/browser_profile")
    web_origins: str = "http://localhost:5173,http://localhost:3000,http://localhost:1420"

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.web_origins.split(",") if origin.strip()]

    def ensure_directories(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.browser_profile_dir.mkdir(parents=True, exist_ok=True)


settings = Settings()