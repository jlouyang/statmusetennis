import logging

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from backend.database.queries import (
    health_check,
    list_players,
    get_player_by_id,
    get_player_matches,
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


@router.get("/players/{player_id}")
def get_player(player_id: str):
    player = get_player_by_id(player_id)
    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Player not found",
        )
    return player


@router.get("/players/{player_id}/matches")
def get_player_match_history(
    player_id: str,
    year: str | None = None,
    surface: str | None = None,
    tournament_level: str | None = None,
    limit: int = 50,
    offset: int = 0,
):
    player = get_player_by_id(player_id)
    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Player not found",
        )
    data = get_player_matches(
        player_id,
        year=year,
        surface=surface,
        tournament_level=tournament_level,
        limit=limit,
        offset=offset,
    )
    return {
        "player_id": player["player_id"],
        "player_name": player["name"],
        "total_matches": data["total_matches"],
        "matches": data["matches"],
    }


class QueryRequest(BaseModel):
    query: str


@router.post("/query")
def post_query(payload: QueryRequest):
    logger.info("POST /api/query payload=%s", payload.query)
    parsed = parse_natural_query(payload.query)
    logger.info("parsed=%s", parsed)
    results = None
    error_message = None

    if not parsed.get("type"):
        error_message = "Unable to determine query type"
    elif parsed["type"] in {"grand_slam_titles", "career_stats", "surface_stats"}:
        if not parsed.get("player"):
            error_message = "Player not recognized"
    elif parsed["type"] == "head_to_head":
        if not parsed.get("player") or not parsed.get("opponent"):
            error_message = "Both players are required for head-to-head queries"
    elif parsed["type"] == "tournament_winner":
        if not parsed.get("filters", {}).get("tournament"):
            error_message = "Tournament name not recognized"

    if error_message:
        logger.info("query_error=%s", error_message)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": error_message, "parsed": parsed},
        )
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

