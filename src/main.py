from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.routes import auth, habits, sessions, stats, users
from src.seed import seed_habits


@asynccontextmanager
async def lifespan(app: FastAPI):
    seed_habits()
    yield


app = FastAPI(title="ThinkBreath API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(habits.router)
app.include_router(sessions.router)
app.include_router(stats.router)
app.include_router(users.router)


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "app": "ThinkBreath",
        "version": "2.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
