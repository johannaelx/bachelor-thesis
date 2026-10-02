from datetime import datetime
from typing import Literal
from sqlalchemy import ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.database import Base


class Message(Base):
    __tablename__ = "messages"
    __table_args__ = (
        UniqueConstraint("session_id", "sequence", name="uq_messages_session_id_sequence"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("sessions.id"))
    sequence: Mapped[int] = mapped_column()
    sender: Mapped[Literal["user", "assistant"]] = mapped_column()
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    item_id: Mapped[int | None] = mapped_column(ForeignKey("items.id"), default=None)
    q: Mapped[int | None] = mapped_column(default=None)

    session: Mapped["Session"] = relationship(back_populates="messages")
    item: Mapped["Item | None"] = relationship(back_populates="messages")
