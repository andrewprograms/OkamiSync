import os
import logging
from logging.handlers import RotatingFileHandler

from flask import Flask, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_socketio import SocketIO
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

db = SQLAlchemy()
login_manager = LoginManager()
socketio = SocketIO(async_mode='eventlet', cors_allowed_origins="*")  # dev-friendly

def create_app():
    app = Flask(__name__, static_folder='static', template_folder='../templates')
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-key')
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        raise RuntimeError(
            "DATABASE_URL is not set. Ensure your .env has a valid MySQL DSN "
            "(e.g., mysql+pymysql://user:pass@host/dbname?charset=utf8mb4)."
        )
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_DIR', 'app/static/data/img')

    # Ensure folders
    os.makedirs(os.getenv('LOG_DIR', 'logs'), exist_ok=True)
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Logging to file
    log_path = os.path.join(os.getenv('LOG_DIR', 'logs'), 'app.log')
    file_handler = RotatingFileHandler(log_path, maxBytes=1_000_000, backupCount=5)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('App starting...')

    # Init extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    socketio.init_app(app, logger=False, engineio_logger=False)

    # Models (import after db)
    from app.model.models import User, Table, MenuCategory, MenuItem, Order, OrderItem

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

    # PWA endpoints (served from static)
    @app.route('/manifest.json')
    def manifest():
        return send_from_directory(app.static_folder, 'manifest.json', mimetype='application/json')

    @app.route('/service-worker.js')
    def sw():
        return send_from_directory(app.static_folder, 'service-worker.js', mimetype='application/javascript')

    # A simple health check
    @app.get('/healthz')
    def healthz():
        return {'status': 'ok'}

    return app
