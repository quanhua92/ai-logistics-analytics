from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    cors_origins: list[str] = ["http://localhost:3000"]
    chat_access_key: str = ""

    # OpenRouter via langchain-openrouter. The key is read under either the
    # idiomatic OPENROUTER_API_KEY or the legacy OPENAI_API_KEY so an existing
    # .env keeps working. See .env.example.
    openrouter_api_key: str = Field(
        default="",
        validation_alias=AliasChoices("OPENROUTER_API_KEY", "OPENAI_API_KEY"),
    )
    openrouter_api_base: str = Field(
        default="",
        validation_alias=AliasChoices(
            "OPENROUTER_API_BASE", "OPENROUTER_BASE_URL", "OPENAI_BASE_URL"
        ),
    )
    # "openrouter/free" auto-routes to any available free model.
    # Override with OPENROUTER_MODEL in .env to pin a specific model.
    openrouter_model: str = "openrouter/free"


settings = Settings()
