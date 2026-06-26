from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "Test Platform"
    DATABASE_URL: str = "postgresql://postgres:postgres@db:5432/testplatform"

    class Config:
        env_file = ".env"


settings = Settings()