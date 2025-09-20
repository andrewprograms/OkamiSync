from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, DateTime, func, Boolean, Integer, Numeric, JSON
from app.db import Base

class Cart(Base):
    __tablename__ = "carts"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    table_id: Mapped[int] = mapped_column(Integer, index=True)
    created_at: Mapped = mapped_column(DateTime(timezone=True), server_default=func.now())

class CartItem(Base):
    __tablename__ = "cart_items"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    cart_id: Mapped[str] = mapped_column(String(36), index=True)
    item_id: Mapped[str] = mapped_column(String(36), index=True)
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    options: Mapped[dict] = mapped_column(JSON, default={})  # selected options with quantities
    notes: Mapped[str | None] = mapped_column(String(280), nullable=True)
    added_by: Mapped[str] = mapped_column(String(64))  # anonymous table user id (ephemeral)
    state: Mapped[str] = mapped_column(String(16), default="in_cart")  # transitions
    created_at: Mapped = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class Order(Base):
    __tablename__ = "orders"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    table_id: Mapped[int] = mapped_column(Integer, index=True)
    state: Mapped[str] = mapped_column(String(16), default="submitted")  # submitted, accepted, in_prep, ready, served, voided, comped
    subtotal: Mapped = mapped_column(Numeric(10,2), default=0)
    tax: Mapped = mapped_column(Numeric(10,2), default=0)
    service_charge: Mapped = mapped_column(Numeric(10,2), default=0)
    discount_total: Mapped = mapped_column(Numeric(10,2), default=0)
    total: Mapped = mapped_column(Numeric(10,2), default=0)
    created_at: Mapped = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    menu_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    ticket_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)  # computed when served

class OrderItem(Base):
    __tablename__ = "order_items"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    order_id: Mapped[str] = mapped_column(String(36), index=True)
    item_id: Mapped[str] = mapped_column(String(36))
    title_snapshot: Mapped[str] = mapped_column(String(255))
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    price_each: Mapped = mapped_column(Numeric(10,2), default=0)
    options: Mapped[dict] = mapped_column(JSON, default={})
    notes: Mapped[str | None] = mapped_column(String(280), nullable=True)
    state: Mapped[str] = mapped_column(String(16), default="submitted")
    created_at: Mapped = mapped_column(DateTime(timezone=True), server_default=func.now())

class OrderEvent(Base):
    __tablename__ = "order_events"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[str] = mapped_column(String(36), index=True)
    order_item_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    actor_user_id: Mapped[str | None] = mapped_column(String(36), nullable=True)   # staff user id
    actor_table_user: Mapped[str | None] = mapped_column(String(64), nullable=True)  # anonymous table user
    action: Mapped[str] = mapped_column(String(32))  # e.g., in_cart, submitted, accepted, etc.
    reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped = mapped_column(DateTime(timezone=True), server_default=func.now())
