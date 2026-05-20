from datetime import date, timedelta

from fastapi import APIRouter, Depends

from src import db
from src.dependencies import get_current_user

router = APIRouter(prefix="/stats", tags=["stats"])


def _compute_streaks(unique_dates: set) -> tuple[int, int]:
    if not unique_dates:
        return 0, 0

    today = date.today()

    # Current streak: walk backwards from today; if today has no completion, start from yesterday
    start = today if today.isoformat() in unique_dates else today - timedelta(days=1)
    current = 0
    day = start
    while day.isoformat() in unique_dates:
        current += 1
        day -= timedelta(days=1)

    # Best streak: longest consecutive run across all history
    sorted_dates = sorted(date.fromisoformat(d) for d in unique_dates)
    best = run = 1
    for i in range(1, len(sorted_dates)):
        if (sorted_dates[i] - sorted_dates[i - 1]).days == 1:
            run += 1
            best = max(best, run)
        else:
            run = 1

    return current, best


@router.get("/summary")
def get_summary(user_id: str = Depends(get_current_user)):
    today = date.today().isoformat()

    completions = list(db.habit_completions.find(
        {"user_id": user_id},
        {"_id": 0, "completed_date": 1},
    ))

    total_practices = len(completions)
    today_count = sum(1 for c in completions if c["completed_date"] == today)

    unique_dates = {c["completed_date"] for c in completions}
    current_streak, best_streak = _compute_streaks(unique_dates)

    sessions_agg = list(db.sessions.aggregate([
        {"$match": {"user_id": user_id, "is_completed": True, "actual_duration": {"$ne": None}}},
        {"$group": {"_id": None, "total_seconds": {"$sum": "$actual_duration"}}},
    ]))
    total_seconds = sessions_agg[0]["total_seconds"] if sessions_agg else 0

    total_habits = db.habits.count_documents(
        {"$or": [{"is_default": True}, {"created_by": user_id}]}
    )

    return {
        "total_practices": total_practices,
        "total_minutes": round(total_seconds / 60),
        "current_streak": current_streak,
        "best_streak": best_streak,
        "today_count": today_count,
        "total_habits": total_habits,
    }


@router.get("/weekly")
def get_weekly(user_id: str = Depends(get_current_user)):
    today = date.today()
    days = [today - timedelta(days=i) for i in range(6, -1, -1)]
    date_strings = [d.isoformat() for d in days]

    completions = list(db.habit_completions.find(
        {"user_id": user_id, "completed_date": {"$in": date_strings}},
        {"_id": 0, "completed_date": 1},
    ))

    counts: dict = {}
    for c in completions:
        counts[c["completed_date"]] = counts.get(c["completed_date"], 0) + 1

    return {
        "days": [
            {
                "date": d.isoformat(),
                "label": d.strftime("%a"),
                "count": counts.get(d.isoformat(), 0),
                "is_today": d == today,
            }
            for d in days
        ]
    }
