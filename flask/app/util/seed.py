import json
import os
from app import db
from app.model.models import User, Role, Table, MenuCategory, MenuItem

def run_seed(json_path='db/sample_menu.json', admin_email='admin@example.com', staff_email='staff@example.com'):
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Users
    if not User.query.filter_by(email=admin_email).first():
        admin = User(email=admin_email, name='Admin', role=Role.admin)
        admin.set_password('admin123')
        db.session.add(admin)

    if not User.query.filter_by(email=staff_email).first():
        staff = User(email=staff_email, name='Staff', role=Role.staff)
        staff.set_password('staff123')
        db.session.add(staff)

    # Tables
    for t in data.get('tables', []):
        if not Table.query.filter_by(code=t['code']).first():
            db.session.add(Table(code=t['code'], label=t['label']))

    # Menu
    name_to_cat = {}
    for cat in data.get('categories', []):
        c = MenuCategory(name=cat['name'], sort_order=cat.get('sort_order', 0))
        db.session.add(c)
        name_to_cat[cat['name']] = c
    db.session.flush()  # ids

    for item in data.get('items', []):
        cat = name_to_cat.get(item['category'])
        if not cat:
            continue
        mi = MenuItem(
            category_id=cat.id,
            name=item['name'],
            description=item.get('description', ''),
            price_cents=item['price_cents'],
            image_url=item.get('image_url', ''),
            is_active=True
        )
        db.session.add(mi)

    db.session.commit()
    return True
