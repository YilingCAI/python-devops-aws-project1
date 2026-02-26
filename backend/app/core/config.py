"""
Production-grade configuration management for FastAPI application.

Supports multiple environments:
- development (local)
- staging
- production

Environment variables are loaded from:
1. System environment (.env files are loaded by main.py via python-dotenv)
2. AWS Secrets Manager (for production)
3. Defaults

All sensitive values must be in AWS Secrets Manager for production.
"""

from typing import List
from enum import Enum
from pydantic import Field
from pydantic_settings import BaseSettings


class Environment(str, Enum):
    """Application environment."""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class Settings(BaseSettings):
    """
    Application settings with environment-aware configuration.

    Loads from .env files in the following order:
    1. .env (git-ignored, environment-specific)
    2. .env.local (git-ignored, local overrides)

    For production, use AWS Secrets Manager instead of .env files.
    """

    # ================================================================
    # ENVIRONMENT & APPLICATION
    # ================================================================
    ENVIRONMENT: Environment = Field(default=Environment.DEVELOPMENT, env="ENVIRONMENT")
    PROJECT_NAME: str = Field(default="myproject", env="PROJECT_NAME")
    APP_VERSION: str = Field(default="1.0.0", env="APP_VERSION")
    DEBUG: bool = Field(default=False, env="DEBUG")
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")

    # ================================================================
    # BACKEND - FASTAPI SERVER
    # ================================================================
    BACKEND_HOST: str = Field(default="0.0.0.0", env="BACKEND_HOST")
    BACKEND_PORT: int = Field(default=8000, env="BACKEND_PORT")
    BACKEND_RELOAD: bool = Field(default=False, env="BACKEND_RELOAD")
    BACKEND_WORKERS: int = Field(default=4, env="BACKEND_WORKERS")

    API_TITLE: str = Field(default="API", env="API_TITLE")
    API_DESCRIPTION: str = Field(default="", env="API_DESCRIPTION")
    API_VERSION: str = Field(default="1.0.0", env="API_VERSION")

    # ================================================================
    # DATABASE - PostgreSQL
    # ================================================================
    DATABASE_USER: str = Field(default="postgres", env="DATABASE_USER")
    DATABASE_PASSWORD: str = Field(default="", env="DATABASE_PASSWORD")
    DATABASE_HOST: str = Field(default="localhost", env="DATABASE_HOST")
    DATABASE_PORT: int = Field(default=5432, env="DATABASE_PORT")
    DATABASE_NAME: str = Field(default="myproject", env="DATABASE_NAME")

    # Connection pool settings for production
    DATABASE_POOL_SIZE: int = Field(default=20, env="DATABASE_POOL_SIZE")
    DATABASE_MAX_OVERFLOW: int = Field(default=10, env="DATABASE_MAX_OVERFLOW")
    DATABASE_POOL_TIMEOUT: int = Field(default=30, env="DATABASE_POOL_TIMEOUT")
    DATABASE_ECHO: bool = Field(default=False, env="DATABASE_ECHO")

    # ================================================================
    # SECURITY - JWT & Sessions
    # ================================================================
    JWT_SECRET_KEY: str = Field(default="", env="JWT_SECRET_KEY")
    JWT_ALGORITHM: str = Field(default="HS256", env="JWT_ALGORITHM")
    JWT_EXPIRE_MINUTES: int = Field(default=60, env="JWT_EXPIRE_MINUTES")
    JWT_REFRESH_EXPIRE_DAYS: int = Field(default=7, env="JWT_REFRESH_EXPIRE_DAYS")

    # ================================================================
    # SECURITY - CORS & Origins
    # ================================================================
    ALLOWED_ORIGINS: str = Field(
        default="http://localhost:4200,http://localhost:3000", env="ALLOWED_ORIGINS"
    )
    CORS_ALLOW_CREDENTIALS: bool = Field(default=True, env="CORS_ALLOW_CREDENTIALS")
    CORS_ALLOW_METHODS: str = Field(
        default="GET,POST,PUT,DELETE,OPTIONS,PATCH", env="CORS_ALLOW_METHODS"
    )
    CORS_ALLOW_HEADERS: str = Field(
        default="Content-Type,Authorization", env="CORS_ALLOW_HEADERS"
    )

    # ================================================================
    # SECURITY - Headers & HTTPS
    # ================================================================
    ENABLE_HTTPS_REDIRECT: bool = Field(default=False, env="ENABLE_HTTPS_REDIRECT")
    ENABLE_HSTS: bool = Field(default=True, env="ENABLE_HSTS")
    HSTS_MAX_AGE: int = Field(default=31536000, env="HSTS_MAX_AGE")
    SECURE_COOKIES: bool = Field(default=False, env="SECURE_COOKIES")

    # ================================================================
    # FRONTEND
    # ================================================================
    FRONTEND_URL: str = Field(default="http://localhost:4200", env="FRONTEND_URL")
    API_BASE_URL: str = Field(default="http://localhost:8000", env="API_BASE_URL")

    # ================================================================
    # LOGGING
    # ================================================================
    LOG_FORMAT: str = Field(default="text", env="LOG_FORMAT")  # text or json
    LOG_OUTPUT: str = Field(default="console", env="LOG_OUTPUT")  # console or file
    LOG_FILE_PATH: str = Field(default="/var/log/app", env="LOG_FILE_PATH")
    LOG_FILE_MAX_BYTES: int = Field(default=10485760, env="LOG_FILE_MAX_BYTES")  # 10MB
    LOG_FILE_BACKUP_COUNT: int = Field(default=10, env="LOG_FILE_BACKUP_COUNT")

    # ================================================================
    # AWS Configuration
    # ================================================================
    AWS_REGION: str = Field(default="us-east-1", env="AWS_REGION")
    AWS_ACCESS_KEY_ID: str = Field(default="", env="AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY: str = Field(default="", env="AWS_SECRET_ACCESS_KEY")
    AWS_SECRETS_MANAGER_SECRET_NAME: str = Field(
        default="", env="AWS_SECRETS_MANAGER_SECRET_NAME"
    )

    # ================================================================
    # MONITORING & OBSERVABILITY
    # ================================================================
    SENTRY_DSN: str = Field(default="", env="SENTRY_DSN")
    DATADOG_API_KEY: str = Field(default="", env="DATADOG_API_KEY")
    ENABLE_METRICS: bool = Field(default=True, env="ENABLE_METRICS")
    METRICS_PORT: int = Field(default=9090, env="METRICS_PORT")

    # ================================================================
    # RATE LIMITING
    # ================================================================
    RATE_LIMIT_ENABLED: bool = Field(default=True, env="RATE_LIMIT_ENABLED")
    RATE_LIMIT_REQUESTS: int = Field(default=100, env="RATE_LIMIT_REQUESTS")
    RATE_LIMIT_WINDOW_SECONDS: int = Field(default=60, env="RATE_LIMIT_WINDOW_SECONDS")

    # ================================================================
    # COMPUTED PROPERTIES
    # ================================================================
    @property
    def DATABASE_URL(self) -> str:
        """Construct database URL from components."""
        return (
            f"postgresql+psycopg2://{self.DATABASE_USER}:"
            f"{self.DATABASE_PASSWORD}@{self.DATABASE_HOST}:"
            f"{self.DATABASE_PORT}/{self.DATABASE_NAME}"
        )

    @property
    def ORIGINS_LIST(self) -> List[str]:
        """Parse comma-separated origins into a list."""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]

    @property
    def CORS_METHODS_LIST(self) -> List[str]:
        """Parse comma-separated CORS methods into a list."""
        return [method.strip() for method in self.CORS_ALLOW_METHODS.split(",")]

    @property
    def CORS_HEADERS_LIST(self) -> List[str]:
        """Parse comma-separated CORS headers into a list."""
        return [header.strip() for header in self.CORS_ALLOW_HEADERS.split(",")]

    @property
    def IS_PRODUCTION(self) -> bool:
        """Check if running in production."""
        return self.ENVIRONMENT == Environment.PRODUCTION

    @property
    def IS_DEVELOPMENT(self) -> bool:
        """Check if running in development."""
        return self.ENVIRONMENT == Environment.DEVELOPMENT

    @property
    def IS_STAGING(self) -> bool:
        """Check if running in staging."""
        return self.ENVIRONMENT == Environment.STAGING

    class Config:
        """Pydantic configuration."""

        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

    def validate_production(self) -> None:
        """
        Validate production-critical settings.
        Call this during application startup.
        """
        if self.IS_PRODUCTION:
            errors = []

            # Check critical settings
            if not self.JWT_SECRET_KEY or self.JWT_SECRET_KEY.startswith("dev-"):
                errors.append("JWT_SECRET_KEY must be set to a production-safe value")

            if not self.DATABASE_PASSWORD:
                errors.append("DATABASE_PASSWORD cannot be empty in production")

            if self.DEBUG:
                errors.append("DEBUG must be False in production")

            if not self.ENABLE_HTTPS_REDIRECT:
                errors.append("ENABLE_HTTPS_REDIRECT should be True in production")

            if not self.SECURE_COOKIES:
                errors.append("SECURE_COOKIES should be True in production")

            if errors:
                raise ValueError(
                    "Production validation failed:\n"
                    + "\n".join(f"- {e}" for e in errors)
                )


# ============================================================================
# Global settings instance
# ============================================================================
settings = Settings()


def get_settings() -> Settings:
    """
    Dependency injection for settings.
    Usage in FastAPI routes: def my_route(config: Settings = Depends(get_settings)):
    """
    return settings
