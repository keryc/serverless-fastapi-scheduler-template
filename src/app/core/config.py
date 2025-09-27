from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    STAGE: str = "dev"
    API_BASE_PATH: str | None = None
    ROOT_PATH: str | None = None


settings = Settings()
