from sqlalchemy import (
    Boolean,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Episode(Base):
    __tablename__ = "episodes"

    __table_args__ = (
        UniqueConstraint(
            "content_group",
            "language",
            name="uq_episode_content_group_language",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    season_id: Mapped[int] = mapped_column(
        ForeignKey("seasons.id", ondelete="CASCADE"),
        index=True,
    )

    episode_number: Mapped[int] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String(255), index=True)
    synopsis: Mapped[str | None] = mapped_column(Text, nullable=True)

    duration_seconds: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    language: Mapped[str] = mapped_column(String(50), index=True)
    content_group: Mapped[str] = mapped_column(String(255), index=True)

    is_published: Mapped[bool] = mapped_column(Boolean, default=False, index=True)

    season = relationship("Season", back_populates="episodes")

    artworks = relationship(
        "Artwork",
        back_populates="episode",
        cascade="all, delete-orphan",
    )