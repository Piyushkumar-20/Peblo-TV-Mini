from sqlalchemy import ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Season(Base):
    __tablename__ = "seasons"

    __table_args__ = (
        UniqueConstraint(
            "show_id",
            "season_number",
            name="uq_season_show_season_number",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    show_id: Mapped[int] = mapped_column(
        ForeignKey("shows.id", ondelete="CASCADE"),
        index=True,
    )

    season_number: Mapped[int] = mapped_column(Integer)

    show = relationship("Show", back_populates="seasons")

    episodes = relationship(
        "Episode",
        back_populates="season",
        cascade="all, delete-orphan",
        order_by="Episode.episode_number",
    )