from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    openai_api_key: str | None = None
    openai_model: str = "gpt-5"
    openai_embedding_model: str = "text-embedding-3-small"

    chunk_size: int = 800
    chunk_overlap: int = 120

    weaviate_host: str | None = "localhost"
    weaviate_port: int = 8091
    weaviate_secure: bool = False
    weaviate_grpc_port: int | None = 8092  # set to a port (e.g., 8092) to enable gRPC; None disables
    weaviate_grpc_secure: bool = False
    weaviate_api_key: str | None = None
    weaviate_class: str = "Chunk"

    # derived
    @property
    def mode(self) -> str:
        return "openai" if self.openai_api_key else "mock"

settings = Settings()  # singleton
