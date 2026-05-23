from datetime import datetime, timezone
from src import db

DEFAULT_HABITS = [
    {
        "slug": "morning-breath",
        "name": "Morning Breathing",
        "category": "Breathwork",
        "accentColor": "#7C3AED",
        "description": "Start your day with a grounding box-breathing session.",
        "is_default": True,
    },
    {
        "slug": "gratitude",
        "name": "Gratitude Practice",
        "category": "Mindfulness",
        "accentColor": "#F59E0B",
        "description": "Pause to reflect on three things you are grateful for.",
        "is_default": True,
    },
    {
        "slug": "evening-reflect",
        "name": "Evening Reflection",
        "category": "Reflection",
        "accentColor": "#06B6D4",
        "description": "Wind down with a mindful review of your day.",
        "is_default": True,
    },
    {
        "slug": "focus-session",
        "name": "Deep Focus Session",
        "category": "Focus",
        "accentColor": "#10B981",
        "description": "Use breathing to clear mental clutter before focused work.",
        "is_default": True,
    },
    {
        "slug": "mindful-walk",
        "name": "Mindful Walk",
        "category": "Movement",
        "accentColor": "#EC4899",
        "description": "Bring full awareness to each step during a short walk.",
        "is_default": True,
    },
]


def seed_habits():
    now = datetime.now(timezone.utc)
    for habit in DEFAULT_HABITS:
        db.habits.update_one(
            {"slug": habit["slug"]},
            {
                "$set": {
                    "name": habit["name"],
                    "category": habit["category"],
                    "accentColor": habit["accentColor"],
                    "description": habit["description"],
                    "is_default": habit["is_default"],
                },
                "$setOnInsert": {"created_at": now},
            },
            upsert=True,
        )
