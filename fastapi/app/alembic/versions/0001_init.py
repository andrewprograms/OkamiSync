"""initial

Revision ID: 0001_init
Revises: 
Create Date: 2025-09-20 00:00:00
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0001_init'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table('users',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('username', sa.String(length=64), nullable=False, unique=True),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('role', sa.String(length=16), nullable=False),
        sa.Column('active', sa.Boolean(), server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'))
    )

    op.create_table('tables',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('name', sa.String(length=64), unique=True),
        sa.Column('opaque_uid', sa.String(length=64), unique=True, index=True),
        sa.Column('active', sa.Boolean(), server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'))
    )

    op.create_table('table_sessions',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('table_id', sa.Integer(), index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('last_seen_at', sa.DateTime(timezone=True), server_default=sa.text('now()'))
    )

    op.create_table('categories',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('parent_id', sa.String(length=36)),
        sa.Column('title_i18n', sa.JSON(), server_default='{}'),
        sa.Column('description_i18n', sa.JSON(), server_default='{}'),
        sa.Column('sort_order', sa.Integer(), server_default='0'),
        sa.Column('active', sa.Boolean(), server_default=sa.text('true'))
    )

    op.create_table('items',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('category_id', sa.String(length=36)),
        sa.Column('title_i18n', sa.JSON(), server_default='{}'),
        sa.Column('description_i18n', sa.JSON(), server_default='{}'),
        sa.Column('price', sa.Numeric(10,2), nullable=False),
        sa.Column('tax_class', sa.String(length=32), server_default='standard'),
        sa.Column('dietary_tags', sa.JSON(), server_default='[]'),
        sa.Column('availability', sa.JSON()),
        sa.Column('sort_order', sa.Integer(), server_default='0'),
        sa.Column('image_path', sa.String(length=255)),
        sa.Column('is_86', sa.Boolean(), server_default=sa.text('false')),
        sa.Column('active', sa.Boolean(), server_default=sa.text('true'))
    )

    op.create_table('option_groups',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('item_id', sa.String(length=36), index=True),
        sa.Column('name_i18n', sa.JSON(), server_default='{}'),
        sa.Column('required', sa.Boolean(), server_default=sa.text('false')),
        sa.Column('min_qty', sa.Integer(), server_default='0'),
        sa.Column('max_qty', sa.Integer(), server_default='3')
    )

    op.create_table('options',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('group_id', sa.String(length=36), index=True),
        sa.Column('name_i18n', sa.JSON(), server_default='{}'),
        sa.Column('price_delta', sa.Numeric(10,2), server_default='0'),
        sa.Column('max_per_item', sa.Integer(), server_default='3'),
        sa.Column('is_exclusion', sa.Boolean(), server_default=sa.text('false'))
    )

    op.create_table('menu_versions',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('version_token', sa.String(length=64), index=True)
    )

    op.create_table('carts',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('table_id', sa.Integer(), index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'))
    )

    op.create_table('cart_items',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('cart_id', sa.String(length=36), index=True),
        sa.Column('item_id', sa.String(length=36)),
        sa.Column('quantity', sa.Integer(), server_default='1'),
        sa.Column('options', sa.JSON(), server_default='{}'),
        sa.Column('notes', sa.String(length=280)),
        sa.Column('added_by', sa.String(length=64)),
        sa.Column('state', sa.String(length=16), server_default='in_cart'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'))
    )

    op.create_table('orders',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('table_id', sa.Integer(), index=True),
        sa.Column('state', sa.String(length=16), server_default='submitted'),
        sa.Column('subtotal', sa.Numeric(10,2), server_default='0'),
        sa.Column('tax', sa.Numeric(10,2), server_default='0'),
        sa.Column('service_charge', sa.Numeric(10,2), server_default='0'),
        sa.Column('discount_total', sa.Numeric(10,2), server_default='0'),
        sa.Column('total', sa.Numeric(10,2), server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('menu_version', sa.String(length=64)),
        sa.Column('ticket_seconds', sa.Integer())
    )

    op.create_table('order_items',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('order_id', sa.String(length=36), index=True),
        sa.Column('item_id', sa.String(length=36)),
        sa.Column('title_snapshot', sa.String(length=255)),
        sa.Column('quantity', sa.Integer(), server_default='1'),
        sa.Column('price_each', sa.Numeric(10,2), server_default='0'),
        sa.Column('options', sa.JSON(), server_default='{}'),
        sa.Column('notes', sa.String(length=280)),
        sa.Column('state', sa.String(length=16), server_default='submitted'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'))
    )

    op.create_table('order_events',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('order_id', sa.String(length=36), index=True),
        sa.Column('order_item_id', sa.String(length=36)),
        sa.Column('actor_user_id', sa.String(length=36)),
        sa.Column('actor_table_user', sa.String(length=64)),
        sa.Column('action', sa.String(length=32)),
        sa.Column('reason', sa.String(length=255)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'))
    )

def downgrade():
    op.drop_table('order_events')
    op.drop_table('order_items')
    op.drop_table('orders')
    op.drop_table('cart_items')
    op.drop_table('carts')
    op.drop_table('menu_versions')
    op.drop_table('options')
    op.drop_table('option_groups')
    op.drop_table('items')
    op.drop_table('categories')
    op.drop_table('table_sessions')
    op.drop_table('tables')
    op.drop_table('users')
