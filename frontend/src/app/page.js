"use client";

import { useState } from "react";

const EXAMPLES = [
  "Federer Grand Slam wins",
  "Federer vs Nadal",
  "Who won Wimbledon 2019?",
  "Djokovic career wins",
  "Nadal clay court record",
];

export default function Home() {
  const [query, setQuery] = useState("");
  const [response, setResponse] = useState("");
  const [loading, setLoading] = useState(false);

  const runQuery = async (text) => {
    const trimmed = text.trim();
    if (!trimmed) {
      return;
    }
    console.log("[ui] submit", { query: trimmed });
    setLoading(true);
    setResponse("");
    try {
      const res = await fetch("/api/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: trimmed }),
      });
      console.log("[ui] response", { status: res.status });
      const text = await res.text();
      if (!res.ok) {
        console.warn("[ui] error body", text);
        setResponse(`HTTP ${res.status}\n${text}`);
        return;
      }
      console.log("[ui] success body", text);
      setResponse(JSON.stringify(JSON.parse(text), null, 2));
    } catch (err) {
      console.error("[ui] request failed", err);
      setResponse(String(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <main style={{ fontFamily: "Arial, sans-serif", margin: 40, maxWidth: 900 }}>
      <h1>Tennis Stats Query</h1>
      <p>Type a natural language query and see the parsed intent + results.</p>

      <form
        onSubmit={(event) => {
          event.preventDefault();
          runQuery(query);
        }}
        style={{ display: "flex", gap: 8, margin: "16px 0" }}
      >
        <input
          type="text"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="e.g., Federer Grand Slam wins"
          style={{ flex: 1, padding: 8, fontSize: 16 }}
        />
        <button type="submit" style={{ padding: "8px 16px", fontSize: 16 }}>
          {loading ? "Loading..." : "Search"}
        </button>
      </form>

      <div style={{ marginBottom: 16 }}>
        {EXAMPLES.map((example) => (
          <button
            key={example}
            type="button"
            onClick={() => {
              setQuery(example);
              runQuery(example);
            }}
            style={{ marginRight: 8, marginBottom: 8, padding: "6px 10px" }}
          >
            {example}
          </button>
        ))}
      </div>

      <h3>Response</h3>
      <pre
        style={{
          background: "#f5f5f5",
          color: "#111",
          padding: 12,
          borderRadius: 6,
          minHeight: 120,
          overflow: "auto",
        }}
      >
        {response}
      </pre>
    </main>
  );
}
