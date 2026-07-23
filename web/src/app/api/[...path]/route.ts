import type { NextRequest } from "next/server";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

const BACKEND_URL = process.env.BACKEND_URL ?? "http://localhost:8000";

/** Forward request headers that the backend cares about. */
function forwardHeaders(req: NextRequest): Record<string, string> {
  const h: Record<string, string> = { "Content-Type": "application/json" };
  const chatKey = req.headers.get("x-chat-key");
  if (chatKey) h["X-Chat-Key"] = chatKey;
  return h;
}

/** Catch-all proxy: forwards /api/* to the backend at runtime.
 *
 * Unlike next.config.ts rewrites (which serialize BACKEND_URL at build time),
 * this Route Handler reads process.env.BACKEND_URL on every request — so the
 * same prebuilt image works with any backend URL (localhost, Docker service
 * name, remote host).
 */
export async function GET(
  req: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  const { path } = await params;
  const target = `${BACKEND_URL}/api/${path.join("/")}${req.nextUrl.search}`;
  const res = await fetch(target, {
    headers: forwardHeaders(req),
    cache: "no-store",
  });
  return new Response(res.body, {
    status: res.status,
    headers: { "Content-Type": res.headers.get("content-type") ?? "application/json" },
  });
}

export async function POST(
  req: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  const { path } = await params;
  const target = `${BACKEND_URL}/api/${path.join("/")}${req.nextUrl.search}`;
  const res = await fetch(target, {
    method: "POST",
    headers: forwardHeaders(req),
    body: await req.text(),
    cache: "no-store",
  });
  return new Response(res.body, {
    status: res.status,
    headers: { "Content-Type": res.headers.get("content-type") ?? "application/json" },
  });
}
