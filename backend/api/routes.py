import logging

from fastapi import APIRouter
from pydantic import BaseModel

from backend.database.queries import (
    health_check,
    list_players,
    get_grand_slam_titles,
    get_head_to_head,
    get_tournament_winner,
    get_career_stats,
    get_surface_stats,
)
from backend.api.query_parser import parse_natural_query

router = APIRouter()
logger = logging.getLogger("statmuse.api")


@router.get("/health")
def get_health():
    return health_check()


@router.get("/players")
def get_players(limit: int = 10):
    return {"players": list_players(limit=limit)}


class QueryRequest(BaseModel):
    query: str


@router.post("/query")
def post_query(payload: QueryRequest):
    logger.info("POST /api/query payload=%s", payload.query)
    parsed = parse_natural_query(payload.query)
    logger.info("parsed=%s", parsed)
    results = None
    if parsed.get("type") == "grand_slam_titles" and parsed.get("player"):
        titles = get_grand_slam_titles(
            parsed["player"], parsed.get("filters", {}).get("surface")
        )
        results = {"count": len(titles), "titles": titles}
    elif (
        parsed.get("type") == "head_to_head"
        and parsed.get("player")
        and parsed.get("opponent")
    ):
        results = get_head_to_head(parsed["player"], parsed["opponent"])
    elif parsed.get("type") == "tournament_winner":
        tournament = parsed.get("filters", {}).get("tournament")
        year = parsed.get("filters", {}).get("year")
        if tournament:
            winners = get_tournament_winner(tournament, year)
            results = {"count": len(winners), "winners": winners}
    elif parsed.get("type") == "career_stats" and parsed.get("player"):
        results = get_career_stats(parsed["player"])
    elif parsed.get("type") == "surface_stats" and parsed.get("player"):
        surface = parsed.get("filters", {}).get("surface")
        if surface:
            results = get_surface_stats(parsed["player"], surface)
    logger.info("results_type=%s", type(results).__name__)
    return {"query": payload.query, "parsed": parsed, "results": results}

