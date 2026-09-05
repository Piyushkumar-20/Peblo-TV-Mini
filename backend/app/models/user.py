from enum import Enum

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class UserRole(str, Enum):
    EDITOR = "editor"
    ADMIN = "admin"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    role: Mapped[UserRole] = mapped_column(default=UserRole.EDITOR)