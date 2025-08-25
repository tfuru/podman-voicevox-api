from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    ADMIN_API_KEY: str
    VOICEVOX_ENGINE_URL: str = "http://voicevox-engine:50021"


settings = Settings()
