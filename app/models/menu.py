from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, DateTime, func, Boolean, Integer, Numeric, JSON
from app.db import Base

class Category(Base):
    __tablename__ = "categories"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    parent_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    title_i18n: Mapped[dict] = mapped_column(JSON, default={})
    description_i18n: Mapped[dict] = mapped_column(JSON, default={})
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    active: Mapped[bool] = mapped_column(Boolean, default=True)

class Item(Base):
    __tablename__ = "items"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    category_id: Mapped[str | None] = mapped_column(String(36), nullable=True)  # can be many-to-many via join in future
    title_i18n: Mapped[dict] = mapped_column(JSON, default={})
    description_i18n: Mapped[dict] = mapped_column(JSON, default={})
    price: Mapped = mapped_column(Numeric(10, 2))
    tax_class: Mapped[str] = mapped_column(String(32), default="standard")
    dietary_tags: Mapped[list[str] | None] = mapped_column(JSON, default=[])
    availability: Mapped[dict | None] = mapped_column(JSON, default=None)  # dayparts, date ranges
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    image_path: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_86: Mapped[bool] = mapped_column(Boolean, default=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True)

class OptionGroup(Base):
    __tablename__ = "option_groups"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    item_id: Mapped[str] = mapped_column(String(36), index=True)
    name_i18n: Mapped[dict] = mapped_column(JSON, default={})
    required: Mapped[bool] = mapped_column(Boolean, default=False)
    min_qty: Mapped[int] = mapped_column(Integer, default=0)
    max_qty: Mapped[int] = mapped_column(Integer, default=3)

class Option(Base):
    __tablename__ = "options"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    group_id: Mapped[str] = mapped_column(String(36), index=True)
    name_i18n: Mapped[dict] = mapped_column(JSON, default={})
    price_delta: Mapped = mapped_column(Numeric(10, 2), default=0)
    max_per_item: Mapped[int] = mapped_column(Integer, default=3)
    is_exclusion: Mapped[bool] = mapped_column(Boolean, default=False)

class MenuVersion(Base):
    __tablename__ = "menu_versions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    created_at: Mapped = mapped_column(DateTime(timezone=True), server_default=func.now())
    version_token: Mapped[str] = mapped_column(String(64), index=True)
