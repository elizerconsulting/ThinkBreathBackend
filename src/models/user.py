from pydantic import BaseModel
from typing import Optional

class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str

class LoginRequest(BaseModel):
    email: str
    password: str

class UpdateUserRequest(BaseModel):
    name: Optional[str] = None
    tagline: Optional[str] = None
    settings: Optional[dict] = None

class ForgotPasswordRequest(BaseModel):
    email: str

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

class RefreshRequest(BaseModel):
    refresh_token: str
