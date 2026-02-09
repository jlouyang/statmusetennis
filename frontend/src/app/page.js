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
  const parserMode = process.env.NEXT_PUBLIC_QUERY_PARSER || "rules";
  const [query, setQuery] = useState("");
  const [response, setResponse] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const runQuery = async (text) => {
    const trimmed = text.trim();
    if (!trimmed) {
      return;
    }
    setLoading(true);
    setResponse(null);
    setError("");
    try {
      const res = await fetch("/api/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: trimmed }),
      });
      const text = await res.text();
      if (!res.ok) {
        setError(`HTTP ${res.status}\n${text}`);
        return;
      }
      setResponse(JSON.parse(text));
    } catch (err) {
      setError(String(err));
    } finally {
      setLoading(false);
    }
  };

  const renderResults = () => {
    if (!response) {
      return null;
    }
    const parsed = response.parsed || {};
    const results = response.results || {};

    if (!parsed.type) {
      return <p>No parsed intent found.</p>;
    }

    if (parsed.type === "grand_slam_titles") {
      return (
        <div>
          <p>
            Grand Slam titles for <strong>{parsed.player || "Unknown"}</strong>
          </p>
          <p>Total: {results.count ?? 0}</p>
          {(results.titles || []).map((title, index) => (
            <div key={`${title.tournament}-${title.date}-${index}`}>
              {title.date} — {title.tournament} vs {title.opponent} ({title.score})
            </div>
          ))}
        </div>
      );
    }

    if (parsed.type === "head_to_head") {
      return (
        <div>
          <p>
            Head to head: {results.player1?.name} ({results.player1?.wins}) vs{" "}
            {results.player2?.name} ({results.player2?.wins})
          </p>
          <p>Total matches: {(results.matches || []).length}</p>
        </div>
      );
    }

    if (parsed.type === "tournament_winner") {
      return (
        <div>
          <p>
            Tournament winners for{" "}
            <strong>{parsed.filters?.tournament || "Unknown"}</strong>
          </p>
          <p>Total: {results.count ?? 0}</p>
          {(results.winners || []).map((winner, index) => (
            <div key={`${winner.tournament}-${winner.date}-${index}`}>
              {winner.date} — {winner.winner} ({winner.score})
            </div>
          ))}
        </div>
      );
    }

    if (parsed.type === "career_stats" || parsed.type === "surface_stats") {
      return (
        <div>
          <p>
            {parsed.type === "surface_stats" ? "Surface stats" : "Career stats"} for{" "}
            <strong>{results.player?.name || "Unknown"}</strong>
          </p>
          <p>
            Matches: {results.total_matches ?? 0}, Wins: {results.wins ?? 0}, Losses:{" "}
            {results.losses ?? 0}, Win%: {results.win_pct ?? 0}
          </p>
          {parsed.type === "surface_stats" && (
            <p>Surface: {results.surface || parsed.filters?.surface || "Unknown"}</p>
          )}
        </div>
      );
    }

    return <pre>{JSON.stringify(response, null, 2)}</pre>;
  };

  return (
    <main style={{ fontFamily: "Arial, sans-serif", margin: 40, maxWidth: 900 }}>
      <h1>Tennis Stats Query</h1>
      <div style={{ color: "#555", marginBottom: 8 }}>
        Parser mode: <strong>{parserMode}</strong>
      </div>
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
      <div
        style={{
          background: "#f5f5f5",
          color: "#111",
          padding: 12,
          borderRadius: 6,
          minHeight: 120,
        }}
      >
        {error && <pre>{error}</pre>}
        {!error && renderResults()}
      </div>
    </main>
  );
}
