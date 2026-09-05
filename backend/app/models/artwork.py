from enum import Enum

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class ArtworkType(str, Enum):
    POSTER = "poster"
    BANNER = "banner"
    THUMBNAIL = "thumbnail"


class Artwork(Base):
    __tablename__ = "artworks"

    id: Mapped[int] = mapped_column(primary_key=True)

    episode_id: Mapped[int] = mapped_column(
        ForeignKey("episodes.id", ondelete="CASCADE"),
        index=True,
    )

    artwork_type: Mapped[ArtworkType] = mapped_column()
    storage_key: Mapped[str] = mapped_column(String(500))

    width: Mapped[int] = mapped_column(Integer)
    height: Mapped[int] = mapped_column(Integer)
    file_size_bytes: Mapped[int] = mapped_column(Integer)

    episode = relationship("Episode", back_populates="artworks")