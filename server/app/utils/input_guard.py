"""Lightweight input guard for the chat endpoint.

First-line defense against prompt injection and DoS. This is a UX/cost filter,
NOT a security boundary — the real boundary is the read-only, allowlisted tool
layer (``app/tools/``): even a fully bypassed prompt can only trigger an allowed
analytics query.

Only genuine abuse is hard-rejected (empty input, oversized input, opaque blobs,
prompt-injection patterns). Greetings and off-topic messages are NOT blocked —
they flow to the model, which the system prompt instructs to respond briefly and
redirect to logistics analytics. A friendly reply beats a 400 error toast.

``guard_input`` returns ``(allowed, reason)``; reason is empty when allowed.
Every pattern is reviewable and tunable below.
"""

from __future__ import annotations

import re

MAX_LEN = 500

# Prompt-injection / jailbreak patterns (matched on whitespace-collapsed text).
_INJECTION = [
    r"(?:ignore|disregard|forget|override|skip)\b.{0,30}?\b(?:instructions?|rules?|prompts?|directives?|system\s+prompt)",
    r"you\s+are\s+(?:now|a|an)\s+(?:dan|developer|root|admin|different|free|unrestricted)",
    r"act\s+as\s+(?:if|a|an)\b",
    r"pretend\s+(?:you\s+are|to\s+be)",
    r"(?:reveal|show|print|repeat|output|leak)\s+(?:your|the)\s+(?:system\s+)?(?:prompt|instructions?|rules?)",
    r"\b(?:dan|jailbreak|god\s*mode|developer\s*mode|root\s*mode)\b",
    r"what\s+are\s+your\s+(?:instructions?|rules?|system\s+prompt)",
    r"from\s+now\s+on\s+you(?:'re|\s+are)?\s+(?:are|will|must|can|shall)\b",
    r"new\s+(?:instructions?|rules?)\s*:",
    r"\bsystem\s+prompt\b",
]
_INJECTION_RE = re.compile("|".join(_INJECTION), re.IGNORECASE)

# A long opaque blob (base64/hex) often smuggles a hidden payload.
_BLOB_RE = re.compile(r"[A-Za-z0-9+/=]{120,}")


def guard_input(question: str) -> tuple[bool, str]:
    """Validate a chat question. Returns ``(allowed, reason)``."""
    q = (question or "").strip()
    if not q:
        return False, "Question is empty."
    if len(q) > MAX_LEN:
        return False, f"Question exceeds the {MAX_LEN}-character limit."
    # Collapse whitespace so newlines can't break the patterns.
    norm = re.sub(r"\s+", " ", q)
    if _BLOB_RE.search(norm):
        return False, "Question contains a suspiciously long opaque token."
    if _INJECTION_RE.search(norm):
        return False, "Question matches a known prompt-injection pattern."
    return True, ""
