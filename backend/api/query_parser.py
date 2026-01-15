from typing import Dict, Optional, Any
import os
import re


PLAYERS = {
    "federer": "Roger Federer",
    "nadal": "Rafael Nadal",
    "djokovic": "Novak Djokovic",
    "murray": "Andy Murray",
}

TOURNAMENTS = {
    "wimbledon": "Wimbledon",
    "australian open": "Australian Open",
    "french open": "French Open",
    "us open": "US Open",
}

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

        for key, name in PLAYERS.items():
            if key in query_lower:
                if result["player"] is None:
                    result["player"] = name
                elif result["opponent"] is None:
                    result["opponent"] = name

        if any(term in query_lower for term in ["grand slam", "major", "majors"]):
            result["type"] = "grand_slam_titles"
        elif any(term in query_lower for term in ["vs", "versus", "head to head", "h2h"]):
            result["type"] = "head_to_head"
        elif "won" in query_lower and any(
            term in query_lower for term in ["wimbledon", "australian", "french", "us open"]
        ):
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

        for key, name in TOURNAMENTS.items():
            if key in query_lower:
                result["filters"]["tournament"] = name
                break

        return result


class LLMQueryParser(BaseQueryParser):
    def parse(self, query: str) -> Dict[str, Any]:
        # Placeholder for future LLM integration.
        return {
            "raw": query,
            "type": None,
            "player": None,
            "opponent": None,
            "filters": {},
        }


def get_query_parser() -> BaseQueryParser:
    provider = os.getenv("QUERY_PARSER", "rules").lower()
    if provider == "llm":
        return LLMQueryParser()
    return RuleBasedQueryParser()


def parse_natural_query(query: str) -> Dict[str, Any]:
    return get_query_parser().parse(query)

