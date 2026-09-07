from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.database import Base

class User(Base):
    __tablename__="users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column()

    progress: Mapped[list["UserItemProgress"]] = relationship(back_populates="user")