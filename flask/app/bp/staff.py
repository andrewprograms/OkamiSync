from datetime import datetime
from flask import Blueprint, render_template, jsonify, request, abort
from flask_login import login_required, current_user
from sqlalchemy import desc
from app import db, socketio
from app.util.decorators import roles_required
from app.model.models import Role, Order, OrderItem, OrderStatus, Table

from flask_socketio import join_room, emit

bp = Blueprint('staff', __name__, url_prefix='/staff')

@bp.route('/')
@login_required
@roles_required(Role.staff, Role.admin)
def dashboard():
    return render_template('staff/dashboard.html')

@bp.get('/api/orders')
@login_required
@roles_required(Role.staff, Role.admin)
def api_orders():
    # latest 50
    orders = Order.query.order_by(desc(Order.created_at)).limit(50).all()
    def to_dict(o: Order):
        return {
            'order_id': o.id,
            'table_code': o.table.code if o.table else None,
            'table_label': o.table.label if o.table else None,
            'status': o.status.value,
            'created_at': o.created_at.isoformat(),
            'items': [i.to_dict() for i in o.items]
        }
    return jsonify([to_dict(o) for o in orders])

@bp.post('/api/order/<int:order_id>/status')
@login_required
@roles_required(Role.staff, Role.admin)
def api_update_status(order_id):
    new_status = request.json.get('status')
    if new_status not in [s.value for s in OrderStatus]:
        abort(400)
    o = Order.query.get_or_404(order_id)
    o.status = OrderStatus(new_status)
    for it in o.items:
        it.status = o.status
    db.session.commit()
    payload = {
        'order_id': o.id,
        'table_code': o.table.code,
        'status': o.status.value,
        'updated_at': o.updated_at.isoformat(),
    }
    # Notify table and staff
    socketio.emit('order_status_update', payload, to=f"table_{o.table.code}")
    socketio.emit('order_status_update', payload, to='kitchen')
    return jsonify({'ok': True, 'order': payload})

# Socket: staff joins kitchen room
from flask_socketio import on
@on('join_kitchen')
def join_kitchen(_data):
    join_room('kitchen')
    emit('presence', {'msg': 'staff_joined'}, to='kitchen')
