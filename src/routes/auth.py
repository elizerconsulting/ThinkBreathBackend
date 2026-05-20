import secrets
from datetime import datetime, timedelta, timezone

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status
from src.dependencies import get_current_user

from src import db
from src.auth_utils import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    hash_token,
    verify_password,
    verify_token_hash,
)
from src.email_utils import send_reset_email
from src.models.user import ForgotPasswordRequest, LoginRequest, RefreshRequest, RegisterRequest, ResetPasswordRequest

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(body: RegisterRequest):
    # 1. Validate input
    if not body.name.strip():
        raise HTTPException(status_code=400, detail="Name is required")
    if "@" not in body.email or "." not in body.email:
        raise HTTPException(status_code=400, detail="Valid email is required")
    if len(body.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")

    # 2. Check email not already taken
    email = body.email.lower().strip()
    if db.users.find_one({"email": email}):
        raise HTTPException(status_code=409, detail="Email already registered")

    # 3. Hash the password
    password_hash = hash_password(body.password)

    # 4. Build the user document
    now      = datetime.now(timezone.utc)
    user_doc = {
        "name":               body.name.strip(),
        "email":              email,
        "password_hash":      password_hash,
        "role":               "user",
        "tagline":            "Mindfulness Practitioner",
        "avatar_url":         None,
        "joined_at":          now,
        "last_active_at":     now,
        "refresh_token_hash": None,
        "achievements":       [],
        "settings": {
            "default_session_duration": 600,
            "notifications":            True,
            "theme":                    "dark",
        },
    }

    # 5. Save to MongoDB
    result  = db.users.insert_one(user_doc)
    user_id = str(result.inserted_id)

    # 6. Generate tokens
    access_token  = create_access_token(user_id)
    refresh_token = create_refresh_token(user_id)

    # 7. Hash the refresh token and store it (SHA-256, not bcrypt — tokens are too long for bcrypt)
    db.users.update_one(
        {"_id": result.inserted_id},
        {"$set": {"refresh_token_hash": hash_token(refresh_token)}},
    )

    # 8. Return tokens + basic user info
    return {
        "access_token":  access_token,
        "refresh_token": refresh_token,
        "token_type":    "bearer",
        "user": {
            "id":    user_id,
            "name":  user_doc["name"],
            "email": user_doc["email"],
        },
    }


@router.post("/login")
def login(body: LoginRequest):
    # 1. Find user by email
    email = body.email.lower().strip()
    user  = db.users.find_one({"email": email})

    # 2. Verify — use a generic message so attackers can't tell which field is wrong
    if not user or not verify_password(body.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    user_id = str(user["_id"])

    # 3. Generate fresh tokens
    access_token  = create_access_token(user_id)
    refresh_token = create_refresh_token(user_id)

    # 4. Rotate refresh token hash + update last active
    db.users.update_one(
        {"_id": user["_id"]},
        {"$set": {
            "refresh_token_hash": hash_token(refresh_token),
            "last_active_at":     datetime.now(timezone.utc),
        }},
    )

    # 5. Return tokens + user info
    return {
        "access_token":  access_token,
        "refresh_token": refresh_token,
        "token_type":    "bearer",
        "user": {
            "id":    user_id,
            "name":  user["name"],
            "email": user["email"],
        },
    }


@router.post("/logout")
def logout(user_id: str = Depends(get_current_user)):
    from bson import ObjectId
    db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"refresh_token_hash": None}},
    )
    return {"message": "logged out"}


@router.post("/refresh")
def refresh(body: RefreshRequest):
    payload = decode_token(body.refresh_token)

    if payload is None or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    user_id = payload.get("sub")
    user = db.users.find_one({"_id": ObjectId(user_id)})

    if not user or not user.get("refresh_token_hash"):
        raise HTTPException(status_code=401, detail="Session expired, please log in again")

    if not verify_token_hash(body.refresh_token, user["refresh_token_hash"]):
        raise HTTPException(status_code=401, detail="Refresh token mismatch")

    access_token  = create_access_token(user_id)
    refresh_token = create_refresh_token(user_id)

    db.users.update_one(
        {"_id": user["_id"]},
        {"$set": {
            "refresh_token_hash": hash_token(refresh_token),
            "last_active_at": datetime.now(timezone.utc),
        }},
    )

    return {
        "access_token":  access_token,
        "refresh_token": refresh_token,
        "token_type":    "bearer",
    }


@router.post("/forgot-password")
def forgot_password(body: ForgotPasswordRequest):
    email = body.email.lower().strip()
    user  = db.users.find_one({"email": email})

    # Always return the same response so callers cannot tell if an email is registered
    _generic_ok = {"message": "If that email is registered, a reset link was sent"}

    if not user:
        return _generic_ok

    raw_token  = secrets.token_urlsafe(32)
    token_hash = hash_token(raw_token)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

    db.users.update_one(
        {"_id": user["_id"]},
        {"$set": {
            "reset_token_hash":    token_hash,
            "reset_token_expires": expires_at,
        }},
    )

    try:
        send_reset_email(user["email"], user["name"], raw_token)
    except HTTPException:
        raise
    except Exception:
        # Roll back the token so a stale hash is not left in the database
        db.users.update_one(
            {"_id": user["_id"]},
            {"$unset": {"reset_token_hash": "", "reset_token_expires": ""}},
        )
        raise HTTPException(status_code=500, detail="Failed to send reset email. Please try again.")

    return _generic_ok


@router.post("/dev/reset-token")
def dev_get_reset_token(body: ForgotPasswordRequest):
    import os
    if os.getenv("ENV", "development") != "development":
        raise HTTPException(status_code=404, detail="Not found")

    email = body.email.lower().strip()
    user  = db.users.find_one({"email": email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    raw_token  = secrets.token_urlsafe(32)
    token_hash = hash_token(raw_token)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

    db.users.update_one(
        {"_id": user["_id"]},
        {"$set": {
            "reset_token_hash":    token_hash,
            "reset_token_expires": expires_at,
        }},
    )

    return {"token": raw_token}


@router.post("/reset-password")
def reset_password(body: ResetPasswordRequest):
    if len(body.new_password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")

    token_hash = hash_token(body.token)
    now        = datetime.now(timezone.utc)

    user = db.users.find_one({
        "reset_token_hash":    token_hash,
        "reset_token_expires": {"$gt": now},
    })

    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired reset link")

    db.users.update_one(
        {"_id": user["_id"]},
        {
            "$set":   {"password_hash": hash_password(body.new_password)},
            "$unset": {"reset_token_hash": "", "reset_token_expires": ""},
        },
    )

    return {"message": "Password updated. You can now sign in."}
