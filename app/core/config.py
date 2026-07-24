from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    DATABASE_URL: str  # obligatorio: definir en .env, sin valor por defecto
    OPENAI_API_KEY: str = ""


@lru_cache()
def get_settings():
    return Settings()


settings = get_settings()
