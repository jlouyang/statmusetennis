from typing import Dict, Optional, Any
import os
import re
import json
import logging
from urllib import request, error


logger = logging.getLogger("statmuse.parser")

class BaseQueryParser:
    def parse(self, query: str) -> Dict[str, Any]:
        raise NotImplementedError


class RuleBasedQueryParser(BaseQueryParser):
    def parse(self, query: str) -> Dict[str, Any]:
        query_lower = query.lower()
        result: Dict[str, Any] = {
            "raw": query,
            "type": None,
            "player": None,
            "opponent": None,
            "filters": {},
        }

        if any(term in query_lower for term in ["grand slam", "major", "majors"]):
            result["type"] = "grand_slam_titles"
        elif any(term in query_lower for term in ["vs", "versus", "head to head", "h2h"]):
            result["type"] = "head_to_head"
        elif "won" in query_lower:
            result["type"] = "tournament_winner"
        elif any(term in query_lower for term in ["career wins", "total titles", "win percentage"]):
            result["type"] = "career_stats"

        if "clay" in query_lower:
            result["filters"]["surface"] = "Clay"
        elif "grass" in query_lower:
            result["filters"]["surface"] = "Grass"
        elif "hard" in query_lower:
            result["filters"]["surface"] = "Hard"

        if result["type"] is None and result.get("player") and result["filters"].get("surface"):
            result["type"] = "surface_stats"

        year_match = re.search(r"\b(19|20)\d{2}\b", query_lower)
        if year_match:
            result["filters"]["year"] = year_match.group()

        return validate_parsed_query(result, query)


class LLMQueryParser(BaseQueryParser):
    def parse(self, query: str) -> Dict[str, Any]:
        # Placeholder for future LLM integration.
        mock = os.getenv("LLM_PARSER_MOCK")
        if mock:
            try:
                parsed = json.loads(mock)
                return validate_parsed_query(parsed, query)
            except json.JSONDecodeError:
                pass

        api_key = os.getenv("LLM_API_KEY")
        if not api_key:
            logger.warning("LLM_API_KEY not set; falling back to rule-based parser")
            return RuleBasedQueryParser().parse(query)

        model = os.getenv("LLM_MODEL", "gemini-1.5-flash")
        try:
            parsed = call_gemini_parser(query, api_key=api_key, model=model)
            if parsed:
                return validate_parsed_query(parsed, query)
        except Exception as exc:
            logger.warning("Gemini parser failed; falling back to rule-based: %s", exc)

        return RuleBasedQueryParser().parse(query)


def get_query_parser() -> BaseQueryParser:
    provider = os.getenv("QUERY_PARSER", "llm").lower()
    if provider == "llm":
        return LLMQueryParser()
    return RuleBasedQueryParser()


def parse_natural_query(query: str) -> Dict[str, Any]:
    return get_query_parser().parse(query)


def validate_parsed_query(parsed: Dict[str, Any], query: str) -> Dict[str, Any]:
    if not isinstance(parsed, dict):
        raise ValueError("Parsed query must be an object")

    allowed_types = {
        "grand_slam_titles",
        "head_to_head",
        "tournament_winner",
        "career_stats",
        "surface_stats",
    }

    normalized: Dict[str, Any] = {
        "raw": parsed.get("raw") or query,
        "type": parsed.get("type"),
        "player": parsed.get("player"),
        "opponent": parsed.get("opponent"),
        "filters": parsed.get("filters") if isinstance(parsed.get("filters"), dict) else {},
    }

    if normalized["type"] not in allowed_types:
        normalized["type"] = None

    for key in list(normalized["filters"].keys()):
        if key not in {"surface", "year", "tournament"}:
            normalized["filters"].pop(key, None)

    return normalized


def call_gemini_parser(query: str, api_key: str, model: str) -> Optional[Dict[str, Any]]:
    schema_hint = {
        "raw": "original query",
        "type": "grand_slam_titles | head_to_head | tournament_winner | career_stats | surface_stats",
        "player": "Full player name or null",
        "opponent": "Full player name or null",
        "filters": {
            "surface": "Hard | Clay | Grass (optional)",
            "year": "YYYY (optional)",
            "tournament": "Tournament name (optional)",
        },
    }

    prompt = (
        "You are a JSON-only parser for tennis stats queries. "
        "Return ONLY a valid JSON object matching this schema:\n"
        f"{json.dumps(schema_hint)}\n\n"
        "Rules:\n"
        "- Use null for unknown fields.\n"
        "- Keep filters empty {} when not present.\n"
        "- Use full player names when possible.\n\n"
        f"Query: {query}"
    )

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    body = json.dumps(
        {
            "contents": [
                {"role": "user", "parts": [{"text": prompt}]},
            ],
            "generationConfig": {
                "responseMimeType": "application/json",
            },
        }
    ).encode("utf-8")

    req = request.Request(url, data=body, method="POST")
    req.add_header("Content-Type", "application/json")

    try:
        with request.urlopen(req, timeout=20) as resp:
            raw = resp.read().decode("utf-8")
    except error.HTTPError as exc:
        try:
            body = exc.read().decode("utf-8")
        except Exception:
            body = ""
        raise RuntimeError(f"Gemini HTTP error: {exc.code} {body}".strip()) from exc
    except error.URLError as exc:
        raise RuntimeError("Gemini network error") from exc

    response = json.loads(raw)
    candidates = response.get("candidates", [])
    if not candidates:
        return None
    parts = candidates[0].get("content", {}).get("parts", [])
    if not parts:
        raise RuntimeError(f"Gemini returned empty content: {raw[:500]}")

    text = "\n".join(part.get("text", "") for part in parts).strip()
    if not text:
        raise RuntimeError(f"Gemini returned empty text: {raw[:500]}")

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            return json.loads(text[start : end + 1])
        raise

