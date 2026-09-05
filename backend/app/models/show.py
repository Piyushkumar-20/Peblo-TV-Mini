from sqlalchemy import Boolean, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Show(Base):
    __tablename__ = "shows"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255), index=True)
    synopsis: Mapped[str | None] = mapped_column(Text, nullable=True)
    categories: Mapped[list[str]] = mapped_column(JSONB, default=list)
    section: Mapped[str | None] = mapped_column(String(100), index=True)
    language: Mapped[str] = mapped_column(String(50), index=True)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, index=True)

    seasons = relationship(
        "Season",
        back_populates="show",
        cascade="all, delete-orphan",
        order_by="Season.season_number",
    )