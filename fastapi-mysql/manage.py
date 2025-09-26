import os, uuid, json, qrcode
import typer
from decimal import Decimal
from pathlib import Path

from app.config import settings
from app.db import execute_sync, fetch_all_sync, fetch_one_sync
from app.auth.passwords import hash_password

cli = typer.Typer(help="Management commands for NorenQR (MySQL)")

USERS_DDL = """
CREATE TABLE IF NOT EXISTS users (
  id CHAR(36) PRIMARY KEY,
  username VARCHAR(64) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  role VARCHAR(16) NOT NULL DEFAULT 'admin',
  active TINYINT(1) NOT NULL DEFAULT 1,
  created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
"""

from app.models.tables import DDL as TABLES_DDL
from app.models.menu import DDL as MENU_DDL
from app.models.orders import DDL as ORDERS_DDL

ALL_DDL = [USERS_DDL, *TABLES_DDL, *MENU_DDL, *ORDERS_DDL]

@cli.command()
def initdb():
    for stmt in ALL_DDL:
        execute_sync(stmt)
    typer.echo("Initialized database schema (MySQL).")

@cli.command()
def seed():
    initdb()
    admin_user = os.getenv("ADMIN_DEFAULT_USER", "admin")
    admin_pass = os.getenv("ADMIN_DEFAULT_PASS", "changemeadmin")
    execute_sync(
        """
        INSERT INTO users (id, username, password_hash, role, active)
        VALUES (%s, %s, %s, 'admin', 1)
        ON DUPLICATE KEY UPDATE username = username
        """,
        (str(uuid.uuid4()), admin_user, hash_password(admin_pass)),
    )
    for i in range(1, 4):
        name = f"T{i}"
        opaque = uuid.uuid4().hex[:16]
        execute_sync(
            """
            INSERT INTO tables (name, opaque_uid, active)
            VALUES (%s, %s, 1)
            ON DUPLICATE KEY UPDATE name = name
            """,
            (name, opaque),
        )
    row = fetch_one_sync("SELECT COUNT(*) AS c FROM categories")
    if (row or {}).get("c", 0) == 0:
        cat_id = str(uuid.uuid4())
        execute_sync(
            """
            INSERT INTO categories (id, parent_id, title_i18n, description_i18n, sort_order, active)
            VALUES (%s, NULL, %s, %s, 0, 1)
            """,
            (
                cat_id,
                json.dumps({"en": "Favorites", "ja": "おすすめ"}),
                json.dumps({}),
            ),
        )
        for j in range(1, 11):
            iid = str(uuid.uuid4())
            execute_sync(
                """
                INSERT INTO items (id, category_id, title_i18n, description_i18n, price,
                                   tax_class, dietary_tags, availability, sort_order,
                                   image_path, is_86, active)
                VALUES (%s, %s, %s, %s, %s,
                        'standard', %s, NULL, %s,
                        NULL, 0, 1)
                """,
                (
                    iid,
                    cat_id,
                    json.dumps({"en": f"Item {j}"}),
                    json.dumps({"en": "Tasty"}),
                    Decimal("10.00"),
                    json.dumps([]),
                    j,
                ),
            )
    typer.echo("Seeded admin, tables, category, items.")

@cli.command()
def qr():
    os.makedirs(settings.qr_output_dir, exist_ok=True)
    rows = fetch_all_sync("SELECT name, opaque_uid FROM tables ORDER BY id")
    for r in rows:
        url = f"{settings.asset_origin}/t/{r['opaque_uid']}"
        img = qrcode.make(url)
        img.save(os.path.join(settings.qr_output_dir, f"{r['name']}.png"))
        typer.echo(f"QR for {r['name']} -> {url}")

@cli.command()
def assets():
    base = Path("static")
    for path in base.rglob("*.*"):
        if path.name.endswith(".map"):
            continue
        data = path.read_bytes()
        h = __import__("hashlib").sha256(data).hexdigest()[:8]
        new = path.with_name(f"{path.stem}.{h}{path.suffix}")
        if not new.exists():
            new.write_bytes(data)
    typer.echo("Assets fingerprinted.")

if __name__ == "__main__":
    cli()
