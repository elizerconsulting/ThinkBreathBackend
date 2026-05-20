from datetime import date, datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Query

from src import db
from src.dependencies import get_current_user
from src.models.habit import ToggleHabitRequest

router = APIRouter(prefix="/habits", tags=["habits"])


@router.get("")
def list_habits(user_id: str = Depends(get_current_user)):
    raw = list(db.habits.find(
        {"$or": [{"is_default": True}, {"created_by": user_id}]},
        {"_id": 0},
    ))
    return {"habits": raw}


@router.get("/completions")
def get_completions(
    from_date: Optional[str] = Query(None, alias="from", description="YYYY-MM-DD"),
    to_date:   Optional[str] = Query(None, alias="to",   description="YYYY-MM-DD"),
    user_id: str = Depends(get_current_user),
):
    query: dict = {"user_id": user_id}
    date_filter: dict = {}
    if from_date:
        date_filter["$gte"] = from_date
    if to_date:
        date_filter["$lte"] = to_date
    if date_filter:
        query["completed_date"] = date_filter

    docs = list(db.habit_completions.find(
        query,
        {"_id": 0, "habit_slug": 1, "completed_date": 1},
    ))

    grouped: dict = {}
    for doc in docs:
        grouped.setdefault(doc["habit_slug"], []).append(doc["completed_date"])

    return {"from": from_date, "to": to_date, "completions": grouped}


@router.post("/{slug}/toggle")
def toggle_habit(slug: str, body: ToggleHabitRequest, user_id: str = Depends(get_current_user)):
    target_date = body.date or date.today().isoformat()

    existing = db.habit_completions.find_one({
        "user_id": user_id,
        "habit_slug": slug,
        "completed_date": target_date,
    })

    if existing:
        db.habit_completions.delete_one({"_id": existing["_id"]})
        completed = False
    else:
        db.habit_completions.insert_one({
            "user_id": user_id,
            "habit_slug": slug,
            "completed_date": target_date,
            "created_at": datetime.now(timezone.utc),
        })
        completed = True

    return {"slug": slug, "date": target_date, "completed": completed}
