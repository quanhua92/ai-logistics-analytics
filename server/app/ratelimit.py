"""Rate limiting for token-spending endpoints (the chat routes).

Currently a GLOBAL per-instance cap (one shared bucket): it protects the
OpenRouter quota/spend from a runaway loop or abuse and is independent of the
ingress — no client-IP parsing, so it behaves the same behind Caddy/nginx
without --proxy-headers. Trade-off: one client can exhaust the budget for
others (acceptable for a gated demo). Once we deploy behind a trusted proxy
that sets X-Forwarded-For AND uvicorn runs with --proxy-headers, switch
key_func to slowapi.util.get_remote_address for a per-client limit.
"""

from __future__ import annotations

from slowapi import Limiter
from slowapi.util import get_remote_address

# Global cap — 30 chat requests/minute per server instance.
CHAT_LIMIT = "30/minute"


def _global_key(request: object) -> str:
    # One shared bucket = per-instance cap (proxy-independent). slowapi inspects
    # the signature and only passes the request when a parameter is named
    # ``request`` — hence the exact name (the arg itself is unused).
    del request
    return "global"


limiter = Limiter(key_func=_global_key)

# Kept for the future per-client upgrade (reliable IP behind a trusted proxy).
get_remote_address = get_remote_address  # noqa: F811 (re-exported for clarity)
