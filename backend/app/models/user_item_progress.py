from datetime import date
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.database import Base

class UserItemProgress(Base):
    __tablename__ = "user_item_progress"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id"), primary_key=True)
    easiness_factor: Mapped[float] = mapped_column()
    interval: Mapped[int] = mapped_column()
    reps_successful: Mapped[int] = mapped_column()
    next_review: Mapped[date | None] = mapped_column(default=None)

    user: Mapped["User"] = relationship(back_populates="progress")
    item: Mapped["Item"] = relationship(back_populates="progress")
