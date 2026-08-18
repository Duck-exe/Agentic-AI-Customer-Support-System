from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str = "sqlite:///./support.db"
    jwt_secret: str = "change-this-to-a-long-random-secret"
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 1440
    llm_api_key: str = ""
    llm_base_url: str = "https://api.openai.com/v1"
    llm_model: str = "gpt-4.1-mini"
    knowledge_base_dir: str = "../../knowledge_base"
    vectorstore_dir: str = "./vectorstore"
    cors_origins: str = "http://localhost:5173"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def kb_path(self) -> Path:
        return (Path(__file__).resolve().parent / self.knowledge_base_dir).resolve()

    @property
    def vector_path(self) -> Path:
        return (Path(__file__).resolve().parent.parent / self.vectorstore_dir).resolve()

settings = Settings()
