from pydantic import BaseModel
from typing import Optional

class StartSessionRequest(BaseModel):
    session_type: str = "box-breathing"
    session_name: str = "Focus Breathing"
    planned_duration: int = 600  # seconds

class EndSessionRequest(BaseModel):
    actual_duration: int
    cycles_completed: int
    is_completed: bool
