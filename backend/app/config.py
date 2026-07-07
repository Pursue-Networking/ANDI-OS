"""Central settings. Everything comes from the environment or repo root .env."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "postgresql://andi:andi@localhost:5432/andi"
    redis_url: str = "redis://localhost:6379/0"

    nvidia_api_key: str = ""
    nvidia_base_url: str = "https://integrate.api.nvidia.com/v1"
    chat_model: str = "nvidia/nemotron-3-ultra-550b-a55b"
    embed_model: str = "nvidia/nv-embedqa-e5-v5"
    embed_dim: int = 1024

    mem0_api_key: str = ""

    backend_api_key: str = "dev-local-key"
    llm_enabled: bool = True


settings = Settings()
