"""Lightweight input guard for the chat endpoint.

First-line defense against prompt injection and off-topic abuse. This is a
UX/cost filter, NOT a security boundary — the real boundary is the read-only,
allowlisted tool layer (``app/tools/``): even a fully bypassed prompt can only
trigger an allowed analytics query. The goal here is to cheaply reject the
obvious junk so tokens aren't spent on it.

``guard_input`` returns ``(allowed, reason)``; reason is empty when allowed.
Every pattern is reviewable and tunable below.
"""

from __future__ import annotations

import re

MAX_LEN = 500
MIN_LEN = 3

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

# A legitimate question must touch the logistics-analytics domain. Tunable.
_DOMAIN_RE = re.compile(
    r"\b(?:order|orders|carrier|carriers|delay|delayed|delays?|deliv\w*|revenue|"
    r"forecast|demand|region|regions?|route|routes?|sku|skus|warehouse|warehouses?|"
    r"client|clients?|status|promo\w*|categor\w+|product|month|monthly|weekly|"
    r"trend|performance|volume|shipment|shipments?|transit|exception|on[\s-]?time|"
    r"quantity|price|value|pareto|percentile|share|market|inventory|stock)\b",
    re.IGNORECASE,
)

# A long opaque blob (base64/hex) often smuggles a hidden payload.
_BLOB_RE = re.compile(r"[A-Za-z0-9+/=]{120,}")


def guard_input(question: str) -> tuple[bool, str]:
    """Validate a chat question. Returns ``(allowed, reason)``."""
    q = (question or "").strip()
    if len(q) < MIN_LEN:
        return False, "Question is too short."
    if len(q) > MAX_LEN:
        return False, f"Question exceeds the {MAX_LEN}-character limit."
    # Collapse whitespace so newlines can't break the patterns.
    norm = re.sub(r"\s+", " ", q)
    if _BLOB_RE.search(norm):
        return False, "Question contains a suspiciously long opaque token."
    if _INJECTION_RE.search(norm):
        return False, "Question matches a known prompt-injection pattern."
    if not _DOMAIN_RE.search(norm):
        return False, "Question is outside the logistics-analytics scope."
    return True, ""
