# okami_sync/app/core/settings.py
from __future__ import annotations

import os
from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import List, Optional

from pydantic import (
    AnyUrl,
    BaseModel,
    Field,
    HttpUrl,
    SecretStr,
    ValidationInfo,
    field_validator,
)
from pydantic_settings import BaseSettings, SettingsConfigDict

# Optional: load layered .env files before Pydantic reads environment.
# We do this to support automatic per-environment overrides like:
# .env (base) -> .env.local (machine overrides) -> .env.development/.env.production/.env.test -> .env.{env}.local
try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None  # If python-dotenv isn't installed, we still work.

# ----- Environment detection & layered .env support -----

class Environment(str, Enum):
    development = "development"
    production = "production"
    test = "test"

def _detect_env() -> Environment:
    # Prefer OKAMI_ENV, fall back to APP_ENV, default to development.
    raw = os.getenv("OKAMI_ENV") or os.getenv("APP_ENV") or "development"
    try:
        return Environment(raw.lower())
    except Exception:
        return Environment.development

def _load_layered_env_files(project_root: Path) -> None:
    """
    Load .env layers in a predictable order.
    Later files override earlier ones.
    """
    if load_dotenv is None:
        return

    env = _detect_env().value

    candidates = [
        project_root / ".env",                  # base for everyone
        project_root / ".env.local",           # developer machine overrides
        project_root / f".env.{env}",          # per-environment
        project_root / f".env.{env}.local",    # per-environment local
    ]
    for f in candidates:
        if f.exists():
            load_dotenv(dotenv_path=f, override=True)

# Assume this file lives at okami_sync/app/core/settings.py
# project_root = .../okami_sync (two parents up from this file)
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_load_layered_env_files(_PROJECT_ROOT)


# ----- Sub-sections for better structure -----

class CorsSettings(BaseModel):
    enabled: bool = Field(default=True)
    allow_origins: List[str] = Field(default_factory=lambda: ["*"])
    allow_credentials: bool = Field(default=False)
    allow_methods: List[str] = Field(default_factory=lambda: ["*"])
    allow_headers: List[str] = Field(default_factory=lambda: ["*"])

    @field_validator("allow_origins")
    @classmethod
    def validate_origins(cls, v: List[str]) -> List[str]:
        # For prod, avoid "*"
        return v


class PostgresDsn(AnyUrl):
    allowed_schemes = {"postgres", "postgresql"}
    user_required = True


class RedisDsn(AnyUrl):
    allowed_schemes = {"redis", "rediss"}
    user_required = False


class SecuritySettings(BaseModel):
    jwt_secret: SecretStr = Field(..., description="HS256 secret or private key material")
    jwt_algorithm: str = Field(default="HS256")
    access_token_ttl_seconds: int = Field(default=60 * 60 * 12)  # 12h
    websocket_join_ttl_seconds: int = Field(default=60)  # short-lived table join token
    allowed_origins_for_tokens: Optional[List[str]] = None


class ObservabilitySettings(BaseModel):
    log_level: str = Field(default="INFO", description="DEBUG, INFO, WARNING, ERROR")
    json_logs: bool = Field(default=True)
    enable_traces: bool = Field(default=False)
    otlp_endpoint: Optional[HttpUrl] = None


# ----- Main Settings -----

class Settings(BaseSettings):
    # General
    app_name: str = Field(default="OkamiSync")
    environment: Environment = Field(default_factory=_detect_env)
    debug: bool = Field(default=False)
    public_url: Optional[HttpUrl] = None  # e.g., https://example.com

    # HTTP server
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000)

    # Databases
    database_url: PostgresDsn = Field(
        ..., description="postgresql://user:pass@host:port/dbname"
    )
    redis_url: RedisDsn = Field(
        "redis://localhost:6379/0", description="redis(s)://host:port/db"
    )

    # Feature Flags / Config
    cors: CorsSettings = Field(default_factory=CorsSettings)
    security: SecuritySettings
    obs: ObservabilitySettings = Field(default_factory=ObservabilitySettings)

    # Pydantic Settings config
    model_config = SettingsConfigDict(
        env_prefix="OKAMI_",           # e.g., OKAMI_DATABASE_URL
        extra="ignore",                # ignore unknown env vars
        validate_default=True,         # ensure defaults validate strictly
        case_sensitive=False,          # env vars case-insensitive
        # We don't set env_file here because we preloaded layered .env files already.
    )

    # ----- Cross-field validation & environment-based tweaks -----

    @field_validator("debug")
    @classmethod
    def default_debug_for_env(cls, v: bool, info: ValidationInfo) -> bool:
        # If not explicitly set, toggle by environment
        environment = info.data.get("environment", Environment.development)
        if "OKAMI_DEBUG" in os.environ:
            return v
        return environment != Environment.production

    @field_validator("cors")
    @classmethod
    def tighten_cors_in_production(cls, v: CorsSettings, info: ValidationInfo) -> CorsSettings:
        env = info.data.get("environment", Environment.development)
        if env == Environment.production and v.allow_origins == ["*"]:
            # Friendly guardrail: require explicit origins in prod
            raise ValueError("CORS allow_origins must not be '*' in production")
        return v


# ----- Global accessor with caching -----

@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Create & cache Settings once per process.
    Use get_settings() everywhere to read configuration.
    """
    return Settings()  # Pydantic reads env (already layered via dotenv)