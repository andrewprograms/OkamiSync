from flask import Blueprint, render_template, request, abort, jsonify
from flask_login import current_user, login_required
from sqlalchemy import asc
from app import db, socketio
from app.model.models import Table, MenuCategory, MenuItem, TableCart, TableCartItem, Order, OrderItem, OrderStatus, table_cart_state

from flask_socketio import join_room, leave_room, emit

bp = Blueprint('table', __name__)

def room_for_table(code: str) -> str:
    return f"table_{code}"

@bp.route('/')
def home():
    # Landing page could explain scanning QR; simple redirect to a demo table if you want
    return render_template('diner/table.html', table=None, categories=[], items=[])

@bp.route('/t/<code>')
def table_page(code):
    table = Table.query.filter_by(code=code).first()
    if not table: abort(404)
    cats = MenuCategory.query.order_by(asc(MenuCategory.sort_order), asc(MenuCategory.name)).all()
    items = MenuItem.query.filter_by(is_active=True).all()
    return render_template('diner/table.html', table=table, categories=cats, items=items)

# --- Socket.IO (table rooms) ---
@socketio.on('join_table')
def on_join_table(data):
    code = data.get('table_code')
    if not code: return
    join_room(room_for_table(code))
    emit('presence', {'msg': 'joined', 'table_code': code}, to=room_for_table(code))

@socketio.on('leave_table')
def on_leave_table(data):
    code = data.get('table_code')
    if not code: return
    leave_room(room_for_table(code))
    emit('presence', {'msg': 'left', 'table_code': code}, to=room_for_table(code))

# --- REST-ish endpoints to manipulate the cart and orders ---
@bp.get('/api/menu')
def api_menu():
    cats = MenuCategory.query.order_by(MenuCategory.sort_order).all()
    out = []
    for c in cats:
        out.append({
            'id': c.id,
            'name': c.name,
            'items': [i.to_dict() for i in c.items if i.is_active]
        })
    return jsonify(out)

def get_or_create_cart(table_id: int, user_id: int|None):
    cart = TableCart.query.filter_by(table_id=table_id, user_id=user_id).first()
    if not cart:
        cart = TableCart(table_id=table_id, user_id=user_id)
        db.session.add(cart)
        db.session.commit()
    return cart

@bp.get('/api/table/<code>/cart')
def api_table_cart(code):
    table = Table.query.filter_by(code=code).first_or_404()
    return jsonify(table_cart_state(table.id))

@bp.post('/api/table/<code>/cart/add')
def api_cart_add(code):
    table = Table.query.filter_by(code=code).first_or_404()
    mi = MenuItem.query.get_or_404(request.json.get('menu_item_id'))
    qty = int(request.json.get('qty', 1))
    notes = (request.json.get('notes') or '').strip()[:500]
    cart = get_or_create_cart(table.id, current_user.id if getattr(current_user, 'is_authenticated', False) else None)
    ci = TableCartItem(cart_id=cart.id, menu_item_id=mi.id, qty=max(1, qty), notes=notes)
    db.session.add(ci)
    db.session.commit()
    payload = table_cart_state(table.id)
    socketio.emit('cart_sync', payload, to=room_for_table(code))
    return jsonify({'ok': True, 'cart': payload})

@bp.post('/api/table/<code>/cart/remove')
def api_cart_remove(code):
    table = Table.query.filter_by(code=code).first_or_404()
    cid = int(request.json.get('cart_item_id'))
    ci = TableCartItem.query.get_or_404(cid)
    # Optional: ensure item belongs to same table
    if ci.cart.table_id != table.id:
        abort(400)
    db.session.delete(ci)
    db.session.commit()
    payload = table_cart_state(table.id)
    socketio.emit('cart_sync', payload, to=room_for_table(code))
    return jsonify({'ok': True, 'cart': payload})

@bp.post('/api/table/<code>/submit')
def api_submit_order(code):
    table = Table.query.filter_by(code=code).first_or_404()
    # Gather all cart items for this table
    carts = TableCart.query.filter_by(table_id=table.id).all()
    if not carts:
        return jsonify({'ok': False, 'error': 'Empty cart'}), 400

    order = Order(table_id=table.id, placed_by_id=current_user.id if getattr(current_user, 'is_authenticated', False) else None)
    db.session.add(order)
    db.session.flush()

    total_items = 0
    for c in carts:
        for it in c.items:
            db.session.add(OrderItem(
                order_id=order.id,
                menu_item_id=it.menu_item_id,
                qty=it.qty,
                notes=it.notes,
                price_cents_at_time=it.menu_item.price_cents
            ))
            total_items += it.qty

    # Clear carts
    for c in carts:
        for it in list(c.items):
            db.session.delete(it)
        db.session.delete(c)

    db.session.commit()

    order_payload = {
        'order_id': order.id,
        'table_code': code,
        'table_label': table.label,
        'status': order.status.value,
        'created_at': order.created_at.isoformat(),
        'items': [oi.to_dict() for oi in order.items]
    }
    # Notify table and staff
    socketio.emit('order_submitted', order_payload, to=room_for_table(code))
    socketio.emit('order_submitted', order_payload, to='kitchen')
    socketio.emit('cart_sync', table_cart_state(table.id), to=room_for_table(code))

    return jsonify({'ok': True, 'order': order_payload})
