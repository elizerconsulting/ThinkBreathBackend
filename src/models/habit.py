from pydantic import BaseModel
from typing import Optional

class ToggleHabitRequest(BaseModel):
    date: Optional[str] = None  # "YYYY-MM-DD", defaults to today if not provided
