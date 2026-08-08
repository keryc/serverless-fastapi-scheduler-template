from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings, loaded from the environment and a local .env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Stage and paths
    STAGE: str = "dev"
    API_BASE_PATH: str | None = None
    ROOT_PATH: str | None = None

    # AWS
    AWS_REGION: str = "us-east-1"

    # API authentication. Empty disables the protected endpoints (503).
    API_BEARER_TOKEN: str = ""


settings = Settings()
