from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration, loaded from environment variables / .env.

    agent_base_url / agent_api_key point at the external Upstage-based
    Agent service. That service is being built by another team member —
    this backend only defines the contract it expects (see
    app/services/agent_client.py) and fails clearly when the endpoint
    is not yet configured, instead of guessing at a real integration.
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    agent_base_url: Optional[str] = None
    agent_api_key: Optional[str] = None
    cors_origins: str = "http://localhost:5173"
    debug: bool = True

    # Upstage Studio document-check Agent — a separate, already-live agent
    # used for the real document upload/verification flow (see
    # app/services/upstage_document_agent.py). Unrelated to agent_base_url.
    upstage_api_key: Optional[str] = None

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
