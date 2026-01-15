import { NextResponse } from "next/server";

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";

export async function POST(request) {
  const body = await request.text();
  try {
    console.log("[proxy] forward", { url: `${BACKEND_URL}/api/query`, body });
    const response = await fetch(`${BACKEND_URL}/api/query`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body,
    });
    const text = await response.text();
    console.log("[proxy] response", { status: response.status, text });
    return new NextResponse(text, {
      status: response.status,
      headers: { "Content-Type": "application/json" },
    });
  } catch (error) {
    console.error("[proxy] error", error);
    return NextResponse.json(
      { error: String(error) },
      { status: 502 }
    );
  }
}
