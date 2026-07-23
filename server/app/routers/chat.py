"""Chat endpoint — natural-language logistics questions via the AI orchestrator.

Optionally gated by the chat access key (prototype-grade): when
``CHAT_ACCESS_KEY`` is set, the client must send its SHA-256 hash in the
``X-Chat-Key`` header, compared in constant time to the server's hash of the
configured key. Empty configured key = open, for local development. A per-IP
rate limit (slowapi) applies on top.
"""

from __future__ import annotations

import hashlib
import json
import secrets
from functools import lru_cache

from fastapi import APIRouter, Header, HTTPException, Request
from fastapi.responses import StreamingResponse

from app import schemas
from app.config import settings
from app.db import DbSession
from app.ratelimit import CHAT_LIMIT, limiter
from app.services import ai_orchestrator
from app.utils import chat_log
from app.utils.input_guard import guard_input

router = APIRouter(prefix="/api", tags=["chat"])


@lru_cache(maxsize=1)
def _valid_key_hashes() -> tuple[str, ...]:
    """SHA-256 hex of each configured chat key.

    ``CHAT_ACCESS_KEY`` may hold a comma-separated list (e.g. ``key1,key2``) so
    keys can be rotated with zero downtime — add the new one alongside the old,
    deploy, then drop the old. Empty / unset = gate off (open, for development).
    """
    raw = settings.chat_access_key or ""
    keys = [k.strip() for k in raw.split(",") if k.strip()]
    return tuple(hashlib.sha256(k.encode()).hexdigest() for k in keys)


def _check_key(x_chat_key: str | None) -> None:
    valid = _valid_key_hashes()
    if not valid:
        return  # open in development (no configured keys)
    # Accept any one of the configured keys; compare each in constant time.
    if not x_chat_key or not any(secrets.compare_digest(str(x_chat_key), h) for h in valid):
        raise HTTPException(status_code=401, detail="invalid or missing access key")


def _sse(event_type: str, data: dict) -> str:
    """Format one Server-Sent Event frame."""
    return f"event: {event_type}\ndata: {json.dumps(data, default=str)}\n\n"


@router.post("/chat", response_model=schemas.ChatResponse)
@limiter.limit(CHAT_LIMIT)
async def chat(
    request: Request,
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
@limiter.limit(CHAT_LIMIT)
async def chat_stream(
    request: Request,
    body: schemas.ChatRequest,
    db: DbSession,
    x_chat_key: str | None = Header(default=None, alias="X-Chat-Key"),
) -> StreamingResponse:
    """Streaming chat via Server-Sent Events.

    Emits typed events: status, tool, token, thinking, done, error. The ``done``
    event carries the same payload as POST /api/chat so streaming and
    non-streaming clients render identically. Guard + key + config checks run
    before the stream starts, so 400/401/429/503 still return as normal JSON.
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


@router.get("/chat")
async def list_conversations() -> list[dict]:
    """List recent conversations (newest first) — open, best-effort."""
    return chat_log.list_conversations()


@router.get("/chat/{conversation_id}")
async def get_conversation(conversation_id: str):
    """Replay one conversation's turns — open, best-effort.

    Returns 404 if the id is unsafe or the file is absent; never crashes on a
    malformed line (those are skipped server-side).
    """
    turns = chat_log.read_conversation(conversation_id)
    if not turns:
        raise HTTPException(status_code=404, detail="conversation not found")
    return {"conversation_id": conversation_id, "turns": turns}
