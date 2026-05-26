from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2"
    CHROMA_PERSIST_DIR: str = "./chroma_db"
    SQLITE_DB_PATH: str = "./finn.db"
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    MAX_CONTEXT_MESSAGES: int = 6
    RAG_TOP_K: int = 3
    RAG_DISTANCE_THRESHOLD: float = 0.65


settings = Settings()
