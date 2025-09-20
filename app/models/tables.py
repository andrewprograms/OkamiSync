from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer, DateTime, func, Boolean
from app.db import Base

class Table(Base):
    __tablename__ = "tables"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(64), unique=True)
    opaque_uid: Mapped[str] = mapped_column(String(64), unique=True, index=True)  # printed in QR link
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped = mapped_column(DateTime(timezone=True), server_default=func.now())

class TableSession(Base):
    __tablename__ = "table_sessions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)  # device session id
    table_id: Mapped[int] = mapped_column(Integer, index=True)
    created_at: Mapped = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_seen_at: Mapped = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
