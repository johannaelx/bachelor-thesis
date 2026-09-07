from datetime import datetime
from typing import Literal
from sqlalchemy import ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.database import Base


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("sessions.id"))
    sender: Mapped[Literal["user", "assistant"]] = mapped_column()
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    item_id: Mapped[int | None] = mapped_column(ForeignKey("items.id"), default=None)

    session: Mapped["Session"] = relationship(back_populates="messages")
    item: Mapped["Item | None"] = relationship(back_populates="messages")
