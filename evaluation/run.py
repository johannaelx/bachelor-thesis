import argparse
import json
import sys
from datetime import datetime

from dotenv import load_dotenv

from backend.app.database import SessionLocal
from evaluation.coherence import create_coherence_metric, evaluate_session_coherence
from evaluation.pipeline import load_ended_sessions


def _iso(dt: datetime | None) -> str | None:
    return dt.isoformat() if dt is not None else None


def session_metadata(session) -> dict:
    return {
        "session_id": session.id,
        "user_id": session.user_id,
        "deck_id": session.deck_id,
        "started_at": _iso(session.started_at),
        "ended_at": _iso(session.ended_at),
        "message_count": len(session.messages),
    }


def main() -> int:
    load_dotenv()

    parser = argparse.ArgumentParser(description="G-Eval dialog coherence for ended sessions")
    parser.add_argument("--session-id", type=int, help="Evaluate a single ended session")
    parser.add_argument(
        "--user-id",
        type=int,
        help="Only evaluate ended sessions for this user",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Load sessions and emit metadata only (no OpenAI calls)",
    )
    args = parser.parse_args()

    db = SessionLocal()
    try:
        sessions = load_ended_sessions(
            db,
            session_id=args.session_id,
            user_id=args.user_id,
        )
    finally:
        db.close()

    if args.session_id is not None and not sessions:
        print(
            json.dumps(
                {
                    "session_id": args.session_id,
                    "error": "Session not found, not ended, or has no messages",
                }
            ),
            file=sys.stderr,
        )
        return 1

    if not sessions:
        print("No ended sessions with messages to evaluate.", file=sys.stderr)
        return 0

    metric = create_coherence_metric() if not args.dry_run else None

    exit_code = 0
    for session in sessions:
        try:
            line = session_metadata(session)
            if args.dry_run:
                line["dry_run"] = True
            else:
                line.update(evaluate_session_coherence(session, metric))
        except Exception as exc:
            exit_code = 1
            line = {**session_metadata(session), "error": str(exc)}
        print(json.dumps(line, ensure_ascii=False))

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
