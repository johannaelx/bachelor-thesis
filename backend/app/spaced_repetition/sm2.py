from math import ceil
from datetime import date, timedelta

VALID_QUALITIES = {0, 2, 5}

def review(
    quality: int,
    easiness_factor: float = 2.5,
    interval: int = 0,
    reps_successful: int = 0,
) -> dict[str, float | int | str | bool]:

    if quality not in VALID_QUALITIES:
        raise ValueError("Nur q=0, q=2 und q=5 zulässig.")
    
    current_date = date.today()
    same_day_repeat = False

    # SM-2 logic
    if quality < 3:
        interval = 1
        reps_successful = 0
    else:
        if reps_successful == 0:
            interval = 1
        elif reps_successful == 1:
            interval = 6
        else: 
            interval = ceil(interval * easiness_factor)

        reps_successful += 1
    
    if quality < 4:
        same_day_repeat = True

    # Easiness Factor
    easiness_factor += 0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)
    easiness_factor = max(1.3, easiness_factor)

    # Date for Next Review
    next_review = current_date + timedelta(days=interval)

    return {
        "easiness_factor": round(easiness_factor, 2),
        "interval": interval,
        "reps_successful": reps_successful,
        "next_review": next_review.isoformat(),
        "same_day_repeat": same_day_repeat,
    }