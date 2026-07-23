"""Chat endpoint — natural-language logistics questions via the AI orchestrator.

Optionally gated by the chat access key: when ``CHAT_ACCESS_KEY`` is set, the
``X-Chat-Key`` header must match (secrets.compare_digest). Empty key = open,
for local development.
"""

from __future__ import annotations

import secrets

from fastapi import APIRouter, Header, HTTPException

from app import schemas
from app.config import settings
from app.db import DbSession
from app.services import ai_orchestrator
from app.utils.input_guard import guard_input

router = APIRouter(prefix="/api", tags=["chat"])


def _check_key(x_chat_key: str | None) -> None:
    expected = settings.chat_access_key
    if not expected:
        return  # open in development
    if not x_chat_key or not secrets.compare_digest(x_chat_key, expected):
        raise HTTPException(status_code=401, detail="invalid or missing access key")


@router.post("/chat", response_model=schemas.ChatResponse)
async def chat(
    body: schemas.ChatRequest,
    db: DbSession,
    x_chat_key: str | None = Header(default=None, alias="X-Chat-Key"),
) -> schemas.ChatResponse:
    _check_key(x_chat_key)
    allowed, reason = guard_input(body.question)
    if not allowed:
        raise HTTPException(status_code=400, detail=reason)
    if not settings.openrouter_api_key:
        raise HTTPException(
            status_code=503,
            detail="AI is not configured — set OPENROUTER_API_KEY in server/.env",
        )
    try:
        result = await ai_orchestrator.ask(body.question, db)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"orchestrator error: {exc}") from exc
    return schemas.ChatResponse(**result)
