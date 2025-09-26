import io
import qrcode
from flask import Blueprint, render_template, request, jsonify, send_file, abort
from flask_login import login_required
from sqlalchemy import asc
from app.util.decorators import roles_required
from app.model.models import Role, MenuCategory, MenuItem, Table
from app import db

bp = Blueprint('admin', __name__, url_prefix='/admin')

@bp.route('/')
@login_required
@roles_required(Role.admin)
def dashboard():
    cats = MenuCategory.query.order_by(asc(MenuCategory.sort_order)).all()
    items = MenuItem.query.order_by(asc(MenuItem.id)).all()
    tables = Table.query.order_by(asc(Table.id)).all()
    return render_template('admin/dashboard.html', categories=cats, items=items, tables=tables)

# --- Tables & QR ---
@bp.post('/api/table')
@login_required
@roles_required(Role.admin)
def create_table():
    code = request.json.get('code', '').strip()
    label = request.json.get('label', '').strip()
    if not code or not label: abort(400)
    if Table.query.filter_by(code=code).first(): abort(409)
    t = Table(code=code, label=label)
    db.session.add(t)
    db.session.commit()
    return jsonify({'ok': True, 'table': {'id': t.id, 'code': t.code, 'label': t.label}})

@bp.get('/qr/<code>.png')
@login_required
@roles_required(Role.admin, Role.staff)
def qr_png(code):
    # QR that opens /t/<code>
    from flask import current_app, url_for
    url = request.host_url.rstrip('/') + '/t/' + code
    img = qrcode.make(url)
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return send_file(buf, mimetype='image/png')

# --- Menu CRUD ---
@bp.post('/api/menu/category')
@login_required
@roles_required(Role.admin)
def add_category():
    name = request.json.get('name', '').strip()
    sort = int(request.json.get('sort_order', 0))
    if not name: abort(400)
    c = MenuCategory(name=name, sort_order=sort)
    db.session.add(c)
    db.session.commit()
    return jsonify({'ok': True, 'category': {'id': c.id, 'name': c.name, 'sort_order': c.sort_order}})

@bp.post('/api/menu/item')
@login_required
@roles_required(Role.admin)
def add_item():
    data = request.json
    mi = MenuItem(
        category_id=int(data['category_id']),
        name=data['name'].strip(),
        description=data.get('description','').strip(),
        price_cents=int(data['price_cents']),
        image_url=data.get('image_url','').strip(),
        is_active=bool(data.get('is_active', True))
    )
    db.session.add(mi)
    db.session.commit()
    return jsonify({'ok': True, 'item': mi.to_dict()})

@bp.put('/api/menu/item/<int:item_id>')
@login_required
@roles_required(Role.admin)
def update_item(item_id):
    mi = MenuItem.query.get_or_404(item_id)
    data = request.json
    if 'category_id' in data: mi.category_id = int(data['category_id'])
    if 'name' in data: mi.name = data['name'].strip()
    if 'description' in data: mi.description = data['description'].strip()
    if 'price_cents' in data: mi.price_cents = int(data['price_cents'])
    if 'image_url' in data: mi.image_url = data['image_url'].strip()
    if 'is_active' in data: mi.is_active = bool(data['is_active'])
    db.session.commit()
    return jsonify({'ok': True, 'item': mi.to_dict()})

@bp.delete('/api/menu/item/<int:item_id>')
@login_required
@roles_required(Role.admin)
def delete_item(item_id):
    mi = MenuItem.query.get_or_404(item_id)
    db.session.delete(mi)
    db.session.commit()
    return jsonify({'ok': True})
