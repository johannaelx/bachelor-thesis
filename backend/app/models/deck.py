from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.database import Base 

class Deck(Base):
    __tablename__ = "decks"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column()

    items: Mapped[list["Item"]] = relationship(back_populates="deck")
    sessions: Mapped[list["Session"]] = relationship(back_populates="deck")