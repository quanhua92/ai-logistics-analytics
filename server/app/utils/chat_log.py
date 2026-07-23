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
