import os, uuid, json, qrcode, asyncio
import typer
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import settings
from app.db import AsyncSessionLocal
from app.auth.passwords import hash_password

cli = typer.Typer()

async def _seed():
    async with AsyncSessionLocal() as session:
        # Create admin user if not exists
        await session.execute(text("""
        INSERT INTO users (id, username, password_hash, role, active)
        VALUES (:id, :u, :p, 'admin', true)
        ON CONFLICT (username) DO NOTHING
        """), {"id": str(uuid.uuid4()), "u": os.getenv("ADMIN_DEFAULT_USER","admin"), "p": hash_password(os.getenv("ADMIN_DEFAULT_PASS","changemeadmin"))})
        # Create tables
        for i in range(1,4):
            opaque = uuid.uuid4().hex[:16]
            await session.execute(text("""
            INSERT INTO tables (name, opaque_uid, active) VALUES (:n,:o,true) ON CONFLICT DO NOTHING
            """), {"n": f"T{i}", "o": opaque})
        # Categories
        cat_id = str(uuid.uuid4())
        await session.execute(text("""
            INSERT INTO categories (id, title_i18n, sort_order, active) VALUES (:id, :title, 0, true)
        """), {"id": cat_id, "title": json.dumps({"en":"Favorites","ja":"おすすめ"})})
        # Items
        for j in range(1,11):
            iid = str(uuid.uuid4())
            await session.execute(text("""
            INSERT INTO items (id, category_id, title_i18n, description_i18n, price, tax_class, dietary_tags, sort_order, active)
            VALUES (:id, :cat, :title, :desc, 10.00, 'standard', '[]', :so, true)
            """), {"id": iid, "cat": cat_id, "title": json.dumps({"en": f"Item {j}"}), "desc": json.dumps({"en": "Tasty"}), "so": j})
        await session.commit()

@cli.command()
def seed():
    asyncio.run(_seed())
    print("Seeded admin, tables, category, items.")

@cli.command()
def qr():
    os.makedirs(settings.qr_output_dir, exist_ok=True)
    async def _qr():
        async with AsyncSessionLocal() as session:
            rows = (await session.execute(text("SELECT name, opaque_uid FROM tables ORDER BY id"))).all()
            for name, opaque in rows:
                url = f"http://localhost:8000/t/{opaque}"
                img = qrcode.make(url)
                img.save(os.path.join(settings.qr_output_dir, f"{name}.png"))
                print(f"QR for {name} -> {url}")
    asyncio.run(_qr())

@cli.command()
def assets():
    # Fingerprint static asset files by content hash (basic; keep original filenames for dev)
    from pathlib import Path
    base = Path('static')
    for path in base.rglob('*.*'):
        if path.name.endswith('.map'): continue
        data = path.read_bytes()
        h = __import__('hashlib').sha256(data).hexdigest()[:8]
        new = path.with_name(f"{path.stem}.{h}{path.suffix}")
        if not new.exists():
            new.write_bytes(data)
    print("Assets fingerprinted (copies created). Update HTML if you want to use hashed names.")

if __name__ == "__main__":
    cli()