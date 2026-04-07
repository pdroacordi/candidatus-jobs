from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://postgres:postgres@localhost:5432/candidatus_jobs"
    api_key: str = "change-me"

    model_config = {"env_file": ".env"}


settings = Settings()
