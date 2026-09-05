from enum import Enum
from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class PublishOutcome(str, Enum):
    SUCCESS = "success"
    FAILED = "failed"


class PublishRun(Base):
    __tablename__ = "publish_runs"

    id: Mapped[int] = mapped_column(primary_key=True)

    triggered_by_user_id: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    show_count: Mapped[int] = mapped_column(Integer, default=0)
    episode_count: Mapped[int] = mapped_column(Integer, default=0)

    outcome: Mapped[PublishOutcome] = mapped_column()

    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )