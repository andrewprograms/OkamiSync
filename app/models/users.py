from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, DateTime, func, Boolean
from app.db import Base

class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(16), default="staff")  # 'staff' or 'admin'
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped = mapped_column(DateTime(timezone=True), server_default=func.now())
