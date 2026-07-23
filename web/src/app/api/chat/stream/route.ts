import type { NextRequest } from "next/server";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

const BACKEND_URL = process.env.BACKEND_URL ?? "http://localhost:8000";

/**
 * Streaming proxy for the chat SSE endpoint.
 *
 * Next.js's `rewrites` proxy buffers responses, which breaks Server-Sent Events
 * (the client receives the whole stream at once). This Route Handler streams
 * the backend's SSE through verbatim instead. The (small) request body is
 * buffered; only the response is streamed.
 */
export async function POST(req: NextRequest) {
  const body = await req.text();
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  const chatKey = req.headers.get("x-chat-key");
  if (chatKey) headers["X-Chat-Key"] = chatKey;

  const upstream = await fetch(`${BACKEND_URL}/api/chat/stream`, {
    method: "POST",
    headers,
    body,
    cache: "no-store",
  });

  if (!upstream.ok || !upstream.body) {
    const text = await upstream.text().catch(() => "");
    return new Response(text || upstream.statusText, {
      status: upstream.status,
      headers: { "Content-Type": "application/json" },
    });
  }

  return new Response(upstream.body, {
    status: upstream.status,
    headers: {
      "Content-Type": "text/event-stream; charset=utf-8",
      "Cache-Control": "no-cache, no-transform",
      Connection: "keep-alive",
      "X-Accel-Buffering": "no",
    },
  });
}
