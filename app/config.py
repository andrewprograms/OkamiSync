from pydantic import BaseModel
import os

class Settings(BaseModel):
    app_name: str = os.getenv("APP_NAME", "NorenQR")
    env: str = os.getenv("ENV", "dev")
    host: str = os.getenv("APP_HOST", "0.0.0.0")
    port: int = int(os.getenv("APP_PORT", "8000"))
    asset_origin: str = os.getenv("ASSET_ORIGIN", "http://localhost:8000")

    database_url: str = os.getenv("DATABASE_URL", "postgresql+asyncpg://norenqr:norenqr@localhost:5432/norenqr")
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    token_key_k1: str = os.getenv("TOKEN_KEY_K1", "dev-k1")
    token_key_k0: str = os.getenv("TOKEN_KEY_K0", "dev-k0")
    session_secret: str = os.getenv("SESSION_SECRET", "dev-session-secret")
    csrf_salt: str = os.getenv("CSRF_SALT", "dev-csrf-salt")

    cookie_domain: str = os.getenv("COOKIE_DOMAIN", "localhost")
    cors_allowlist: str = os.getenv("CORS_ALLOWLIST", "http://localhost:8000")

    csp_default_src: str = os.getenv("CSP_DEFAULT_SRC", "'self'")
    csp_img_src: str = os.getenv("CSP_IMG_SRC", "'self' data:")
    csp_connect_src: str = os.getenv("CSP_CONNECT_SRC", "'self'")

    currency: str = os.getenv("CURRENCY", "USD")
    locale_default: str = os.getenv("LOCALE_DEFAULT", "en")
    locales: str = os.getenv("LOCALES", "en,ja")

    media_root: str = os.getenv("MEDIA_ROOT", "./media")
    media_base_url: str = os.getenv("MEDIA_BASE_URL", "/media")
    media_sign_key: str = os.getenv("MEDIA_SIGN_KEY", "dev-media-sign")

    rate_limit_public: str = os.getenv("RATE_LIMIT_PUBLIC", "30/minute")

    qr_output_dir: str = os.getenv("QR_OUTPUT_DIR", "./qr")

settings = Settings()
