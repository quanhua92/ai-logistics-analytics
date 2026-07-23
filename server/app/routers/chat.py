"""Chat endpoint — natural-language logistics questions via the AI orchestrator.

Optionally gated by the chat access key: when ``CHAT_ACCESS_KEY`` is set, the
``X-Chat-Key`` header must match (secrets.compare_digest). Empty key = open,
for local development.
"""

from __future__ import annotations

import json
import secrets

from fastapi import APIRouter, Header, HTTPException
from fastapi.responses import StreamingResponse

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


def _sse(event_type: str, data: dict) -> str:
    """Format one Server-Sent Event frame."""
    return f"event: {event_type}\ndata: {json.dumps(data, default=str)}\n\n"


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
        result = await ai_orchestrator.ask(
            body.question, db, history=body.history, conversation_id=body.conversation_id
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"orchestrator error: {exc}") from exc
    return schemas.ChatResponse(**result)


@router.post("/chat/stream")
async def chat_stream(
    body: schemas.ChatRequest,
    db: DbSession,
    x_chat_key: str | None = Header(default=None, alias="X-Chat-Key"),
) -> StreamingResponse:
    """Streaming chat via Server-Sent Events.

    Emits typed events: status, tool, token, done, error. The ``done`` event
    carries the same payload as POST /api/chat so streaming and non-streaming
    clients render identically. Guard + key + config checks run before the
    stream starts, so 400/401/503 still return as normal JSON errors.
    """
    _check_key(x_chat_key)
    allowed, reason = guard_input(body.question)
    if not allowed:
        raise HTTPException(status_code=400, detail=reason)
    if not settings.openrouter_api_key:
        raise HTTPException(
            status_code=503,
            detail="AI is not configured — set OPENROUTER_API_KEY in server/.env",
        )

    async def event_gen():
        try:
            async for ev in ai_orchestrator.ask_stream(
                body.question, db, history=body.history, conversation_id=body.conversation_id
            ):
                payload = {k: v for k, v in ev.items() if k != "type"}
                yield _sse(ev["type"], payload)
        except Exception as exc:  # belt-and-suspenders: ask_stream already guards
            yield _sse("error", {"detail": f"{type(exc).__name__}: {exc}"})

    return StreamingResponse(event_gen(), media_type="text/event-stream")
