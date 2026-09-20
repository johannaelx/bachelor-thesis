from datetime import date
from sqlalchemy.orm import Session

from backend.app.models.user_item_progress import UserItemProgress
from backend.app.spaced_repetition.sm2 import review as sm2_review


def get_or_create_progress(db: Session, user_id: int, item_id: int) -> UserItemProgress:
    """Returns existing UserItemProgress or creates a new one with SM-2 defaults."""
    progress = db.get(UserItemProgress, (user_id, item_id))
    if progress is None:
        progress = UserItemProgress(
            user_id=user_id,
            item_id=item_id,
            easiness_factor=2.5,
            interval=0,
            reps_successful=0,
            next_review=None,
        )
        db.add(progress)
        db.flush()
    return progress


def apply_and_save_review(db: Session, user_id: int, item_id: int, q: int) -> dict:
    """Runs SM-2 for a given user/item/quality and persists the result."""
    progress = get_or_create_progress(db, user_id, item_id)

    result = sm2_review(
        quality=q,
        easiness_factor=progress.easiness_factor,
        interval=progress.interval,
        reps_successful=progress.reps_successful,
    )

    progress.easiness_factor = result["easiness_factor"]
    progress.interval = result["interval"]
    progress.reps_successful = result["reps_successful"]
    progress.next_review = result["next_review"]

    db.commit()
    return result
