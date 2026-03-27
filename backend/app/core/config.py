from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = Field(default="Real Estate Intelligence API", alias="APP_NAME")
    environment: str = Field(default="dev", alias="ENVIRONMENT")
    database_url: str = Field(
        default="sqlite:///./realestate.db",
        alias="DATABASE_URL",
    )
    allowed_origins: str = Field(
        default="http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173,http://localhost:5174,http://127.0.0.1:5174",
        alias="ALLOWED_ORIGINS",
    )
    allowed_origin_regex: str = Field(default="", alias="ALLOWED_ORIGIN_REGEX")
    auth_secret_key: str = Field(default="change-me-in-production", alias="AUTH_SECRET_KEY")
    auth_algorithm: str = Field(default="HS256", alias="AUTH_ALGORITHM")
    auth_access_token_minutes: int = Field(default=60 * 12, alias="AUTH_ACCESS_TOKEN_MINUTES")
    rate_limit_per_minute: int = Field(default=120, alias="RATE_LIMIT_PER_MINUTE")
    abs_api_url: str = Field(default="", alias="ABS_API_URL")
    licensed_feed_url: str = Field(default="", alias="LICENSED_FEED_URL")

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
