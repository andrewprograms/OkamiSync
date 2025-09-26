# run once in a Python shell with FLASK_APP=main.py context
from app import create_app, db
from app.util.seed import run_seed
app = create_app()
with app.app_context():
    run_seed('db/sample_menu.json')
