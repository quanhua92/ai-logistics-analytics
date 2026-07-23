from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from sqlalchemy import text

from app.config import settings
from app.db import DbSession, create_db_lifespan
from app.ratelimit import limiter
from app.routers import chat, dashboard, forecast

app = FastAPI(
    title="AI Logistics Analytics API",
    lifespan=create_db_lifespan(settings.database_url),
)

# Rate limiting (per-IP) — registered so @limiter.limit on routes works.
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(dashboard.router)
app.include_router(chat.router)
app.include_router(forecast.router)


@app.get("/api/health")
async def health(db: DbSession):
    await db.execute(text("SELECT 1"))
    return {"status": "ok", "db": "connected"}
