from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    openai_api_key: str | None = None
    openai_model: str = "gpt-5"
    openai_embedding_model: str = "text-embedding-3-small"

    chunk_size: int = 800
    chunk_overlap: int = 120

    redis_url: str = "redis://localhost:6379"
    redis_password: str | None = None
    redis_index: str = "rag:chunks"

    # derived
    @property
    def mode(self) -> str:
        return "openai" if self.openai_api_key else "mock"

settings = Settings()  # singleton
