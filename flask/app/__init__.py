import os
import logging
from logging.handlers import RotatingFileHandler
from urllib.parse import quote_plus

from flask import Flask, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_socketio import SocketIO
from dotenv import load_dotenv, find_dotenv, dotenv_values

# Load .env from project root even if launched elsewhere
load_dotenv(find_dotenv())
_DOTENV_MAP = dotenv_values(find_dotenv()) or {}

db = SQLAlchemy()
login_manager = LoginManager()
socketio = SocketIO(async_mode="eventlet", cors_allowed_origins="*")  # dev-friendly


def _truthy(v) -> bool:
    return str(v).strip().lower() in {"1", "true", "yes", "y", "on"}


def _get_any(keys, default=None):
    """
    Return the first non-empty value from os.environ or .env (supports hyphenated keys).
    Example: _get_any(['LOCAL_SQL_USER', 'local-sql-user-name'])
    """
    for key in keys:
        val = os.getenv(key)
        if val:
            return val
        # fallback to .env map (supports keys that aren't valid env var names, e.g. with '-')
        if key in _DOTENV_MAP and _DOTENV_MAP[key]:
            return _DOTENV_MAP[key]
        # try underscore <-> hyphen swap for robustness
        if "-" in key:
            alt = key.replace("-", "_")
            val = os.getenv(alt) or _DOTENV_MAP.get(alt)
            if val:
                return val
        if "_" in key:
            alt = key.replace("_", "-")
            val = os.getenv(alt) or _DOTENV_MAP.get(alt)
            if val:
                return val
    return default


def _compose_mysql_url(user, password, host, port, dbname):
    """
    Compose a safe SQLAlchemy URL for PyMySQL. We URL-encode user, password and dbname
    so special characters like @ : / # don't break parsing.
    """
    if not (user and password and host and dbname):
        return None
    port = str(port or "3306")
    user_q = quote_plus(str(user))
    pass_q = quote_plus(str(password))
    db_q = quote_plus(str(dbname))
    return f"mysql+pymysql://{user_q}:{pass_q}@{host}:{port}/{db_q}?charset=utf8mb4"


def _resolve_database_url():
    """
    Resolution priority:
      1) DATABASE_URL / MYSQL_URL / SQLALCHEMY_DATABASE_URI (explicit override)
      2) FLASK_ENV=development  -> compose from LOCAL_* (with hyphen aliases + common synonyms)
      3) FLASK_ENV!=development -> compose from PA_*    (with hyphen aliases + common synonyms)

    Supported synonyms (examples):
      - LOCAL_SQL_USER, MYSQL_USER, DB_USER
      - LOCAL_SQL_PASSWORD, MYSQL_PASSWORD, DB_PASSWORD
      - LOCAL_SQL_DB, MYSQL_DB / MYSQL_DATABASE, DB_NAME
      - LOCAL_SQL_HOST, MYSQL_HOST, DB_HOST
      - LOCAL_SQL_PORT, MYSQL_PORT, DB_PORT
      - production: PA_SQL_* / PA_MYSQL_* / MYSQL_* / DB_*
    """
    # 1) Explicit override wins
    explicit = _get_any(["DATABASE_URL", "MYSQL_URL", "SQLALCHEMY_DATABASE_URI"])
    if explicit:
        return explicit

    env = (_get_any(["FLASK_ENV"], "production") or "production").lower()

    if env == "development":
        user = _get_any(
            [
                "LOCAL_SQL_USER",
                "LOCAL_DB_USER",
                "APP_DB_USER",
                "MYSQL_USER",
                "DB_USER",
                "local-sql-user-name",
                "local-sql-username",
            ]
        )
        password = _get_any(
            [
                "LOCAL_SQL_PASSWORD",
                "LOCAL_DB_PASSWORD",
                "APP_DB_PASSWORD",
                "MYSQL_PASSWORD",
                "DB_PASSWORD",
                "local-sql-user-password",
                "local-sql-password",
            ]
        )
        host = _get_any(
            ["LOCAL_SQL_HOST", "MYSQL_HOST", "DB_HOST", "local-sql-host"], "127.0.0.1"
        )
        port = _get_any(["LOCAL_SQL_PORT", "MYSQL_PORT", "DB_PORT", "local-sql-port"], "3306")
        dbname = _get_any(
            [
                "LOCAL_SQL_DB",
                "LOCAL_DB_NAME",
                "MYSQL_DB",
                "MYSQL_DATABASE",
                "DB_NAME",
                "local-sql-db",
                "local-sql-database-name",
            ]
        )
        return _compose_mysql_url(user, password, host, port, dbname)

    # production / default path (PythonAnywhere etc.)
    user = _get_any(["PA_SQL_USER", "PA_MYSQL_USER", "MYSQL_USER", "pa-mysql-user", "DB_USER"])
    password = _get_any(
        ["PA_SQL_PASSWORD", "PA_MYSQL_PASSWORD", "MYSQL_PASSWORD", "pa-mysql-password", "DB_PASSWORD"]
    )
    host = _get_any(["PA_SQL_HOST", "PA_MYSQL_HOST", "MYSQL_HOST", "pa-mysql-host", "DB_HOST"])
    port = _get_any(["PA_SQL_PORT", "PA_MYSQL_PORT", "MYSQL_PORT", "pa-mysql-port", "DB_PORT"], "3306")
    dbname = _get_any(
        ["PA_SQL_DB", "PA_MYSQL_DB", "MYSQL_DB", "MYSQL_DATABASE", "pa-mysql-db", "pa-mysql-database", "DB_NAME"]
    )
    return _compose_mysql_url(user, password, host, port, dbname)


def create_app():
    app = Flask(__name__, static_folder="static", template_folder="../templates")

    # App config
    app.config["APP_NAME"] = _get_any(["APP_NAME"], "QR Ordering")
    app.config["SECRET_KEY"] = _get_any(["SECRET_KEY"], "dev-key")

    # Logging to file
    log_dir = _get_any(["LOG_DIR"], "logs")
    upload_dir = _get_any(["UPLOAD_DIR"], "app/static/data/img")
    os.makedirs(log_dir, exist_ok=True)
    os.makedirs(upload_dir, exist_ok=True)
    log_path = os.path.join(log_dir, "app.log")
    file_handler = RotatingFileHandler(log_path, maxBytes=1_000_000, backupCount=5)
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    )
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)

    # Database URL resolution (antifragile)
    db_url = _resolve_database_url()
    if not db_url:
        raise RuntimeError(
            "Could not resolve a database URL. Either set DATABASE_URL, or provide "
            "LOCAL_SQL_* (development) or PA_SQL_*/pa-mysql-* (production) variables in .env."
        )

    app.config["SQLALCHEMY_DATABASE_URI"] = db_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_pre_ping": True,
        "pool_recycle": 280,  # avoid stale connections
    }
    app.config["UPLOAD_FOLDER"] = upload_dir

    # Init extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    socketio.init_app(app, logger=False, engineio_logger=False)

    # Models
    from app.model.models import (
        User,
        Table,
        MenuCategory,
        MenuItem,
        Order,
        OrderItem,
    )  # noqa

    # Optionally create tables on boot (can be disabled for tooling)
    if _truthy(_get_any(["AUTO_CREATE_TABLES"], "1")):
        with app.app_context():
            db.create_all()

    # Blueprints
    from app.bp.auth import bp as auth_bp
    from app.bp.table import bp as table_bp
    from app.bp.staff import bp as staff_bp
    from app.bp.admin import bp as admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(table_bp)
    app.register_blueprint(staff_bp)
    app.register_blueprint(admin_bp)

    # PWA endpoints
    @app.route("/manifest.json")
    def manifest():
        return send_from_directory(
            app.static_folder, "manifest.json", mimetype="application/json"
        )

    @app.route("/service-worker.js")
    def sw():
        return send_from_directory(
            app.static_folder, "service-worker.js", mimetype="application/javascript"
        )

    @app.get("/healthz")
    def healthz():
        return {"status": "ok"}

    # Log which DB we're using (passwords sanitized)
    try:
        sanitized = db_url
        for secret in filter(
            None,
            [
                _get_any(
                    [
                        "LOCAL_SQL_PASSWORD",
                        "local-sql-user-password",
                        "local-sql-password",
                        "MYSQL_PASSWORD",
                        "DB_PASSWORD",
                    ]
                ),
                _get_any(["PA_SQL_PASSWORD", "PA_MYSQL_PASSWORD", "pa-mysql-password"]),
            ],
        ):
            sanitized = sanitized.replace(secret, "***")
        app.logger.info(
            "FLASK_ENV=%s • Using DB: %s",
            _get_any(["FLASK_ENV"], "production"),
            sanitized,
        )
    except Exception:
        pass

    return app
