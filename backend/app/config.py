from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    openrouter_api_key: str | None = None
    openrouter_model: str = "openai/gpt-4o-mini"
    vaani_api_key: str | None = None
    vaani_voice_id: str | None = None
    vaani_agent_id: str | None = None
    vaani_api_base_url: str = "https://api.vaanivoice.ai"
    public_base_url: str | None = None
    vaani_webhook_secret: str | None = None
    cors_origins: str = "http://localhost:3000"


settings = Settings()
