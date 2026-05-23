from fastapi import APIRouter, Depends, HTTPException
from bson import ObjectId
from src.dependencies import get_current_user
from src.models.user import UpdateUserRequest
from src import db

router = APIRouter(prefix="/users", tags=["users"])


def _serialize_user(user: dict, user_id: str) -> dict:
    joined = user.get("joined_at")
    return {
        "id": user_id,
        "name": user["name"],
        "email": user["email"],
        "tagline": user.get("tagline", ""),
        "avatar_url": user.get("avatar_url"),
        "joined_at": joined.isoformat() if joined else None,
        "achievements": user.get("achievements", []),
        "settings": user.get("settings", {}),
    }


@router.get("/me")
def get_me(user_id: str = Depends(get_current_user)):
    user = db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return _serialize_user(user, user_id)


@router.patch("/me")
def update_me(body: UpdateUserRequest, user_id: str = Depends(get_current_user)):
    updates = body.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    db.users.update_one({"_id": ObjectId(user_id)}, {"$set": updates})

    user = db.users.find_one({"_id": ObjectId(user_id)})
    return _serialize_user(user, user_id)
