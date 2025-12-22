from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):

    APP_NAME: str

    NEO4J_URI: str
    NEO4J_USERNAME: str
    NEO4J_PASSWORD: str
    NEO4J_DATABASE: str
    AURA_INSTANCEID: str
    AURA_INSTANCENAME: str

    DAFAULT_OUTPUT_MAX_TOKENS: Optional[int] = None
    DAFAULT_TEMPERATURE: Optional[float] = None
    
    GENERATION_BACKEND: str
    EMBEDDING_BACKEND: str
    GENERATION_MODEL_ID: Optional[str] = None
    EMBEDDING_MODEL_ID: Optional[str] = None
    EMBEDDING_MODEL_DIMENSION: Optional[str] = None

    COHERE_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None

    VECTOR_DB_BACKEND: str
    QDRANT_DB_PATH: Optional[str] = None
    QDRANT_CACHE_PATH: Optional[str] = None
    VECTOR_DB_DISTANCE_METHOD: Optional[str] = None

    PRIMARY_LANG: Optional[str] = None
    DEFAULT_LANG: str

    class Config:
        env_file = ".env"


def get_settings():
    return Settings()