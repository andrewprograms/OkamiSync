import enum
from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import Enum, func
from app import db, login_manager

class Role(enum.Enum):
    user = "user"
    staff = "staff"
    admin = "admin"

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    name = db.Column(db.String(120), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(Enum(Role), nullable=False, default=Role.user)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, pw): self.password_hash = generate_password_hash(pw)
    def check_password(self, pw): return check_password_hash(self.password_hash, pw)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class Table(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(64), unique=True, nullable=False)  # used in QR/URL
    label = db.Column(db.String(64), nullable=False)  # e.g. "Table A"

class MenuCategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    sort_order = db.Column(db.Integer, default=0)

class MenuItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey('menu_category.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, default="")
    price_cents = db.Column(db.Integer, nullable=False)
    image_url = db.Column(db.String(512), default="")
    is_active = db.Column(db.Boolean, default=True)
    category = db.relationship('MenuCategory', backref='items')

    def to_dict(self):
        return {
            'id': self.id,
            'category': self.category.name if self.category else None,
            'name': self.name,
            'description': self.description,
            'price_cents': self.price_cents,
            'image_url': self.image_url,
            'is_active': self.is_active,
        }

class OrderStatus(enum.Enum):
    submitted = "submitted"
    acknowledged = "acknowledged"
    preparing = "preparing"
    ready = "ready"
    served = "served"
    cancelled = "cancelled"

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    table_id = db.Column(db.Integer, db.ForeignKey('table.id'), nullable=False)
    placed_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    status = db.Column(Enum(OrderStatus), default=OrderStatus.submitted, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    table = db.relationship('Table')
    placed_by = db.relationship('User')

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    menu_item_id = db.Column(db.Integer, db.ForeignKey('menu_item.id'), nullable=False)
    qty = db.Column(db.Integer, nullable=False, default=1)
    notes = db.Column(db.String(500), default="")
    price_cents_at_time = db.Column(db.Integer, nullable=False)
    status = db.Column(Enum(OrderStatus), default=OrderStatus.submitted, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    order = db.relationship('Order', backref='items')
    menu_item = db.relationship('MenuItem')

    def to_dict(self):
        return {
            'id': self.id,
            'menu_item_id': self.menu_item_id,
            'name': self.menu_item.name if self.menu_item else '',
            'qty': self.qty,
            'notes': self.notes,
            'price_cents': self.price_cents_at_time,
            'status': self.status.value
        }

# A lightweight table-scoped cart for real-time collaboration
class TableCart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    table_id = db.Column(db.Integer, db.ForeignKey('table.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    table = db.relationship('Table')
    user = db.relationship('User')

class TableCartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cart_id = db.Column(db.Integer, db.ForeignKey('table_cart.id'), nullable=False)
    menu_item_id = db.Column(db.Integer, db.ForeignKey('menu_item.id'), nullable=False)
    qty = db.Column(db.Integer, nullable=False, default=1)
    notes = db.Column(db.String(500), default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    cart = db.relationship('TableCart', backref='items')
    menu_item = db.relationship('MenuItem')

def cents_to_str(cents: int) -> str:
    return f"${cents/100:.2f}"

def table_cart_state(table_id: int):
    """Aggregate current cart by user and overall for a table."""
    carts = TableCart.query.filter_by(table_id=table_id).all()
    users = {c.user_id: (c.user.name if c.user else "Guest") for c in carts}
    per_user = {}
    total_cents = 0
    items_flat = []
    for c in carts:
        ui = []
        for it in c.items:
            price = it.menu_item.price_cents if it.menu_item else 0
            total_cents += price * it.qty
            entry = {
                'cart_item_id': it.id,
                'menu_item_id': it.menu_item_id,
                'name': it.menu_item.name if it.menu_item else '',
                'qty': it.qty,
                'notes': it.notes,
                'price_cents': price
            }
            ui.append(entry)
            items_flat.append(entry)
        per_user[c.user_id or 0] = {
            'user_label': users.get(c.user_id, 'Guest'),
            'items': ui
        }
    return {
        'per_user': per_user,
        'all_items': items_flat,
        'total_cents': total_cents,
        'total_str': cents_to_str(total_cents)
    }
