"""Per-conversation chat logging for debugging.

Each conversation (identified by a client-generated UUID) appends one JSONL line
per turn to ``{chat_log_dir}/{uuid}.jsonl``. Best-effort: logging never raises
into the request path. Configurable via ``CHAT_LOG_DIR`` (gitignored).
"""

from __future__ import annotations

import datetime as _dt
import json
import os
from typing import Any

from app.config import settings


def _safe_path(conversation_id: str) -> str | None:
    """Resolve the conversation file path, rejecting path traversal.

    The id must be a simple token (alnum/dash/underscore) AND the resolved real
    path must live inside the chat-log directory — two independent checks so
    neither one alone is trusted.
    """
    if not conversation_id:
        return None
    if not all(c.isalnum() or c in "-_" for c in conversation_id):
        return None
    directory = os.path.realpath(settings.chat_log_dir or ".chat-logs")
    candidate = os.path.realpath(os.path.join(directory, f"{conversation_id}.jsonl"))
    try:
        if os.path.commonpath([directory, candidate]) != directory:
            return None
    except ValueError:
        return None  # different drives / incomparable paths
    return candidate


def append_turn(conversation_id: str | None, record: dict[str, Any]) -> None:
    """Append one turn record to the conversation's JSONL file."""
    if not conversation_id:
        return
    directory = settings.chat_log_dir or ".chat-logs"
    try:
        os.makedirs(directory, exist_ok=True)
        line = {
            "ts": _dt.datetime.now(_dt.timezone.utc).isoformat(),
            "conversation_id": conversation_id,
            **record,
        }
        with open(os.path.join(directory, f"{conversation_id}.jsonl"), "a", encoding="utf-8") as f:
            f.write(json.dumps(line, default=str) + "\n")
    except Exception:
        # Logging is best-effort; never break the chat over it.
        pass


def read_conversation(conversation_id: str) -> list[dict[str, Any]]:
    """Best-effort read of a conversation's turns. Never raises; skips bad lines."""
    path = _safe_path(conversation_id)
    if not path or not os.path.isfile(path):
        return []
    turns: list[dict[str, Any]] = []
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except (json.JSONDecodeError, ValueError):
                    continue  # skip unparseable line — best effort
                if isinstance(obj, dict):
                    turns.append(obj)
    except Exception:
        pass
    return turns


def list_conversations() -> list[dict[str, Any]]:
    """Best-effort summary of all conversations, newest first. Never raises."""
    directory = settings.chat_log_dir or ".chat-logs"
    if not os.path.isdir(directory):
        return []
    try:
        files = sorted(
            (os.path.join(directory, f) for f in os.listdir(directory) if f.endswith(".jsonl")),
            key=os.path.getmtime,
            reverse=True,
        )
    except Exception:
        return []
    out: list[dict[str, Any]] = []
    for path in files:
        cid = os.path.splitext(os.path.basename(path))[0]
        turns = read_conversation(cid)
        if not turns:
            continue
        out.append(
            {
                "conversation_id": cid,
                "first_question": str(turns[0].get("question", ""))[:120],
                "turn_count": len(turns),
                "last_ts": str(turns[-1].get("ts", "")),
            }
        )
    return out

