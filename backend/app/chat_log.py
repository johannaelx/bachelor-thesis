from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.app.models.message import Message
from backend.app.models.session import Session as LearningSession


def create_learning_session(db: Session, user_id: int, deck_id: int) -> LearningSession:
    """Opens a learning session for a user and deck."""
    learning_session = LearningSession(user_id=user_id, deck_id=deck_id)
    db.add(learning_session)
    db.flush()
    return learning_session


def add_message(
    db: Session,
    session_id: int,
    sender: str,
    content: str,
    item_id: int | None = None,
    q: int | None = None,
) -> Message:
    """Appends one chat message."""
    current = (
        db.query(func.max(Message.sequence))
        .filter(Message.session_id == session_id)
        .scalar()
    )
    message = Message(
        session_id=session_id,
        sequence=(current or 0) + 1,
        sender=sender,
        content=content,
        item_id=item_id,
        q=q,
    )
    db.add(message)
    db.flush()
    return message


def end_learning_session(db: Session, session_id: int) -> LearningSession | None:
    """Sets ended_at once."""
    learning_session = db.get(LearningSession, session_id)
    if learning_session is None:
        return None
    if learning_session.ended_at is None:
        learning_session.ended_at = datetime.utcnow()
        db.commit()
    return learning_session
