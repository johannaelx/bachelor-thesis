from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.database import Base

class Item(Base):
    __tablename__ = "items"

    id: Mapped[int] = mapped_column(primary_key=True)
    german: Mapped[str] = mapped_column()
    english: Mapped[str] = mapped_column()
    deck_id: Mapped[int] = mapped_column(ForeignKey("decks.id"))

    deck: Mapped["Deck"] = relationship(back_populates="items")
    progress: Mapped[list["UserItemProgress"]] = relationship(back_populates="item")