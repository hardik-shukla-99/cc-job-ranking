from pydantic_settings import BaseSettings
from sqlalchemy import URL


class Settings(BaseSettings):
    LOG_LEVEL: str = "DEBUG"
    ENV: str = "local"
    APP_NAME: str = "Cc Job Ranking API"
    APP_VERSION: str = "0.1.0"

    # Database
    DB_USER: str | None = None
    DB_PASSWORD: str | None = None
    DB_HOST: str | None = None
    DB_PORT: int = 5432
    DB_NAME: str | None = None
    DB_ECHO: bool = False

    CORS_ALLOWED_URL: str | None = None

    # Internal service-to-service auth
    INTERNAL_TOKEN: str | None = None

    def validate_env_variables(self) -> None:
        required = {
            "DB_USER": self.DB_USER,
            "DB_PASSWORD": self.DB_PASSWORD,
            "DB_HOST": self.DB_HOST,
            "DB_NAME": self.DB_NAME,
            "CORS_ALLOWED_URL": self.CORS_ALLOWED_URL,
        }
        missing = [k for k, v in required.items() if not v]
        if missing:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing)}"
            )

    @property
    def db_url(self) -> URL:
        return URL.create(
            drivername="postgresql",
            username=self.DB_USER,
            host=self.DB_HOST,
            port=self.DB_PORT,
            database=self.DB_NAME,
            password=self.DB_PASSWORD,
        )

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


settings = Settings()
if settings.ENV not in ("test", "unittest"):
    settings.validate_env_variables()
