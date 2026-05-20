from datetime import datetime, timezone

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException

from src import db
from src.dependencies import get_current_user
from src.models.session import EndSessionRequest, StartSessionRequest

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("/start")
def start_session(body: StartSessionRequest, user_id: str = Depends(get_current_user)):
    now = datetime.now(timezone.utc)
    doc = {
        "user_id": user_id,
        "session_type": body.session_type,
        "session_name": body.session_name,
        "planned_duration": body.planned_duration,
        "started_at": now,
        "ended_at": None,
        "actual_duration": None,
        "cycles_completed": None,
        "is_completed": False,
    }
    result = db.sessions.insert_one(doc)
    return {
        "session_id": str(result.inserted_id),
        "session_type": body.session_type,
        "session_name": body.session_name,
        "planned_duration": body.planned_duration,
        "started_at": now.isoformat(),
    }


@router.patch("/{session_id}/end")
def end_session(session_id: str, body: EndSessionRequest, user_id: str = Depends(get_current_user)):
    try:
        oid = ObjectId(session_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid session_id")

    session = db.sessions.find_one({"_id": oid, "user_id": user_id})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    now = datetime.now(timezone.utc)
    db.sessions.update_one(
        {"_id": oid},
        {"$set": {
            "actual_duration": body.actual_duration,
            "cycles_completed": body.cycles_completed,
            "is_completed": body.is_completed,
            "ended_at": now,
        }},
    )
    return {
        "session_id": session_id,
        "actual_duration": body.actual_duration,
        "cycles_completed": body.cycles_completed,
        "is_completed": body.is_completed,
        "ended_at": now.isoformat(),
    }
