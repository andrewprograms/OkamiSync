#!/usr/bin/env python
"""
Database management helpers for the QR Ordering app.

Usage (run inside your venv):
  python tools/db_manage.py info           # show env + URL (no DB connect)
  python tools/db_manage.py test           # try to connect; prints version/current_user
  python tools/db_manage.py create         # create tables
  python tools/db_manage.py seed           # seed sample data
  python tools/db_manage.py reset          # drop + create + seed
  python tools/db_manage.py seed --file db/sample_menu.json  # custom seed file
"""
import os
import sys
import argparse
from dotenv import load_dotenv, find_dotenv
from sqlalchemy import text

# Ensure .env is loaded regardless of CWD
load_dotenv(find_dotenv())

# Ensure project root is importable when run from tools/
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# Prevent automatic db.create_all() when importing the app
os.environ.setdefault("AUTO_CREATE_TABLES", "0")

from app import create_app, db, _resolve_database_url  # noqa: E402


def _sanitized_db_url(url: str) -> str:
    if not url:
        return "<unset>"
    for key in ("LOCAL_SQL_PASSWORD", "PA_SQL_PASSWORD", "MYSQL_PASSWORD", "DB_PASSWORD"):
        pw = os.getenv(key)
        if pw:
            url = url.replace(pw, "***")
    return url


def cmd_info(_args):
    url = _resolve_database_url()
    print(f"FLASK_ENV: {os.getenv('FLASK_ENV', 'production')}")
    print(f"Database:  {_sanitized_db_url(url)}")


def cmd_test(_args):
    app = create_app()
    with app.app_context():
        try:
            ver = db.session.execute(text("SELECT VERSION()")).scalar()
            who = db.session.execute(text("SELECT CURRENT_USER()")).scalar()
            print("✅ Connected to MySQL")
            print(f"  version: {ver}")
            print(f"  current_user: {who}")
        except Exception as e:
            print("❌ Connection failed:")
            print(f"  {e}")


def cmd_create(_args):
    app = create_app()
    with app.app_context():
        db.create_all()
    print("✅ Tables created.")


def cmd_seed(args):
    app = create_app()
    json_path = args.file or "db/sample_menu.json"
    if not os.path.exists(json_path):
        raise SystemExit(f"Seed file not found: {json_path}")
    from app.util.seed import run_seed  # lazy import inside app context
    with app.app_context():
        ok = run_seed(json_path)
        if ok:
            print(f"✅ Seeded from {json_path}")
        else:
            print("⚠️  Seeding reported no changes")


def cmd_reset(_args):
    app = create_app()
    with app.app_context():
        db.drop_all()
        db.create_all()
        print("✅ Dropped and recreated tables.")
        from app.util.seed import run_seed
        run_seed("db/sample_menu.json")
        print("✅ Seeded from db/sample_menu.json")


def main():
    parser = argparse.ArgumentParser(description="DB management for QR Ordering")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("info", help="Show which DB the app will use (no connect)")
    sub.add_parser("test", help="Attempt a DB connection and print version/user")
    sub.add_parser("create", help="Create tables (no drop)")

    p_seed = sub.add_parser("seed", help="Seed sample data")
    p_seed.add_argument("--file", "-f", help="Path to seed JSON (default: db/sample_menu.json)")

    sub.add_parser("reset", help="Drop + create + seed (DANGER)")

    args = parser.parse_args()
    if args.cmd == "info":
        cmd_info(args)
    elif args.cmd == "test":
        cmd_test(args)
    elif args.cmd == "create":
        cmd_create(args)
    elif args.cmd == "seed":
        cmd_seed(args)
    elif args.cmd == "reset":
        cmd_reset(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
