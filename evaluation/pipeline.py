from sqlalchemy.orm import Session, joinedload, selectinload

from backend.app.models.message import Message
from backend.app.models.session import Session as LearningSession
from deepeval.test_case import ConversationalTestCase, Turn


def load_ended_sessions(
    db: Session,
    *,
    session_id: int | None = None,
    user_id: int | None = None,
    require_messages: bool = True,
) -> list[LearningSession]:
    """Loads ended learning sessions with messages, user and deck."""
    query = (
        db.query(LearningSession)
        .options(
            selectinload(LearningSession.messages),
            joinedload(LearningSession.user),
            joinedload(LearningSession.deck),
        )
        .filter(LearningSession.ended_at.isnot(None))
        .order_by(LearningSession.id)
    )

    if session_id is not None:
        query = query.filter(LearningSession.id == session_id)

    if user_id is not None:
        query = query.filter(LearningSession.user_id == user_id)

    sessions = query.all()

    if require_messages:
        sessions = [s for s in sessions if s.messages]

    return sessions


def build_conversational_test_case(messages: list[Message]) -> ConversationalTestCase:
    ordered = sorted(messages, key=lambda message: message.sequence)
    turns = [
        Turn(
            role="user" if message.sender == "user" else "assistant",
            content=message.content,
        )
        for message in ordered
    ]
    return ConversationalTestCase(turns=turns)
