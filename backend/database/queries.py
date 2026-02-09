from typing import Any, Dict, List, Optional

from sqlalchemy import text

from .db import get_connection


def health_check() -> Dict[str, Any]:
    with get_connection() as conn:
        row = conn.execute(text("SELECT 1 AS ok")).mappings().fetchone()
    return {"ok": bool(row["ok"]) if row else False}


def list_players(limit: int = 10) -> List[Dict[str, Any]]:
    with get_connection() as conn:
        rows = (
            conn.execute(
                text("SELECT player_id, name FROM players ORDER BY name LIMIT :limit"),
                {"limit": limit},
            )
            .mappings()
            .fetchall()
        )
    return [dict(row) for row in rows]


def get_player_by_id(player_id: str) -> Optional[Dict[str, Any]]:
    with get_connection() as conn:
        row = (
            conn.execute(
                text(
                    """
                    SELECT player_id, name, hand, birth_date, country
                    FROM players
                    WHERE player_id = :player_id
                    """
                ),
                {"player_id": player_id},
            )
            .mappings()
            .fetchone()
        )
    return dict(row) if row else None


def get_player_matches(
    player_id: str,
    year: Optional[str] = None,
    surface: Optional[str] = None,
    tournament_level: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> Dict[str, Any]:
    query = """
        SELECT
            m.date AS date,
            t.name AS tournament,
            m.surface AS surface,
            m.round AS round,
            m.score AS score,
            CASE
                WHEN m.winner_id = p.player_id THEN 'W'
                ELSE 'L'
            END AS result,
            opp.name AS opponent
        FROM matches m
        JOIN players p
            ON (m.player1_id = p.player_id OR m.player2_id = p.player_id)
        JOIN players opp
            ON (
                (m.player1_id = opp.player_id OR m.player2_id = opp.player_id)
                AND opp.player_id != p.player_id
            )
        JOIN tournaments t
            ON m.tournament_id = t.tournament_id
        WHERE p.player_id = :player_id
    """
    params: Dict[str, Any] = {"player_id": player_id}

    if year:
        query += " AND m.date LIKE :year"
        params["year"] = f"{year}%"
    if surface:
        query += " AND m.surface = :surface"
        params["surface"] = surface
    if tournament_level:
        query += " AND t.level = :tournament_level"
        params["tournament_level"] = tournament_level

    count_query = f"SELECT COUNT(*) AS total FROM ({query}) AS subquery"

    query += " ORDER BY m.date DESC LIMIT :limit OFFSET :offset"
    params_with_paging = {**params, "limit": limit, "offset": offset}

    with get_connection() as conn:
        total_row = (
            conn.execute(text(count_query), params).mappings().fetchone()
        )
        rows = (
            conn.execute(text(query), params_with_paging)
            .mappings()
            .fetchall()
        )

    return {
        "total_matches": int(total_row["total"]) if total_row else 0,
        "matches": [dict(row) for row in rows],
    }


def get_grand_slam_titles(
    player_name: str, surface: Optional[str] = None
) -> List[Dict[str, Any]]:
    query = """
        SELECT
            t.name AS tournament,
            m.date AS date,
            m.score AS score,
            p2.name AS opponent
        FROM matches m
        JOIN players p1
            ON (m.player1_id = p1.player_id OR m.player2_id = p1.player_id)
        JOIN players p2
            ON (m.player1_id = p2.player_id OR m.player2_id = p2.player_id)
        JOIN tournaments t
            ON m.tournament_id = t.tournament_id
        WHERE p1.name = :player_name
            AND m.winner_id = p1.player_id
            AND p2.player_id != p1.player_id
            AND t.level = 'G'
            AND m.round = 'F'
    """
    params: Dict[str, Any] = {"player_name": player_name}
    if surface:
        query += " AND m.surface = :surface"
        params["surface"] = surface
    query += " ORDER BY m.date"

    with get_connection() as conn:
        rows = conn.execute(text(query), params).mappings().fetchall()
    return [dict(row) for row in rows]


def get_head_to_head(player1_name: str, player2_name: str) -> Dict[str, Any]:
    with get_connection() as conn:
        player1_row = (
            conn.execute(
                text("SELECT player_id, name FROM players WHERE name = :name"),
                {"name": player1_name},
            )
            .mappings()
            .fetchone()
        )
        player2_row = (
            conn.execute(
                text("SELECT player_id, name FROM players WHERE name = :name"),
                {"name": player2_name},
            )
            .mappings()
            .fetchone()
        )

        if not player1_row or not player2_row:
            return {
                "player1": {"id": None, "name": player1_name, "wins": 0},
                "player2": {"id": None, "name": player2_name, "wins": 0},
                "matches": [],
                "by_surface": {},
            }

        query = """
            SELECT
                m.date AS date,
                t.name AS tournament,
                m.surface AS surface,
                m.round AS round,
                m.winner_id AS winner_id,
                m.score AS score
            FROM matches m
            JOIN tournaments t
                ON m.tournament_id = t.tournament_id
            WHERE (m.player1_id = :player1_id AND m.player2_id = :player2_id)
               OR (m.player1_id = :player2_id AND m.player2_id = :player1_id)
            ORDER BY m.date DESC
        """
        rows = (
            conn.execute(
                text(query),
                {
                    "player1_id": player1_row["player_id"],
                    "player2_id": player2_row["player_id"],
                },
            )
            .mappings()
            .fetchall()
        )

    matches = [dict(row) for row in rows]
    player1_wins = 0
    player2_wins = 0
    by_surface: Dict[str, Dict[str, int]] = {}

    for match in matches:
        surface = match.get("surface") or "Unknown"
        if surface not in by_surface:
            by_surface[surface] = {"player1_wins": 0, "player2_wins": 0}
        if match.get("winner_id") == player1_row["player_id"]:
            player1_wins += 1
            by_surface[surface]["player1_wins"] += 1
        elif match.get("winner_id") == player2_row["player_id"]:
            player2_wins += 1
            by_surface[surface]["player2_wins"] += 1

    return {
        "player1": {
            "id": player1_row["player_id"],
            "name": player1_row["name"],
            "wins": player1_wins,
        },
        "player2": {
            "id": player2_row["player_id"],
            "name": player2_row["name"],
            "wins": player2_wins,
        },
        "matches": matches,
        "by_surface": by_surface,
    }


def get_tournament_winner(
    tournament_name: str, year: Optional[str] = None
) -> List[Dict[str, Any]]:
    query = """
        SELECT
            t.name AS tournament,
            m.date AS date,
            p.name AS winner,
            m.score AS score
        FROM matches m
        JOIN tournaments t
            ON m.tournament_id = t.tournament_id
        JOIN players p
            ON m.winner_id = p.player_id
        WHERE LOWER(t.name) = LOWER(:tournament_name)
            AND m.round = 'F'
    """
    params: Dict[str, Any] = {"tournament_name": tournament_name}
    if year:
        query += " AND m.date LIKE :year"
        params["year"] = f"{year}%"
    query += " ORDER BY m.date DESC"

    with get_connection() as conn:
        rows = conn.execute(text(query), params).mappings().fetchall()
    return [dict(row) for row in rows]


def get_career_stats(player_name: str) -> Dict[str, Any]:
    with get_connection() as conn:
        player_row = (
            conn.execute(
                text("SELECT player_id, name FROM players WHERE name = :name"),
                {"name": player_name},
            )
            .mappings()
            .fetchone()
        )
        if not player_row:
            return {
                "player": {"id": None, "name": player_name},
                "total_matches": 0,
                "wins": 0,
                "losses": 0,
                "win_pct": 0.0,
            }

        total_matches_row = (
            conn.execute(
                text(
                    """
                    SELECT COUNT(*) AS total
                    FROM matches
                    WHERE player1_id = :player_id OR player2_id = :player_id
                    """
                ),
                {"player_id": player_row["player_id"]},
            )
            .mappings()
            .fetchone()
        )
        wins_row = (
            conn.execute(
                text(
                    """
                    SELECT COUNT(*) AS wins
                    FROM matches
                    WHERE winner_id = :player_id
                    """
                ),
                {"player_id": player_row["player_id"]},
            )
            .mappings()
            .fetchone()
        )

    total_matches = int(total_matches_row["total"]) if total_matches_row else 0
    wins = int(wins_row["wins"]) if wins_row else 0
    losses = max(total_matches - wins, 0)
    win_pct = round((wins / total_matches) * 100, 2) if total_matches else 0.0

    return {
        "player": {"id": player_row["player_id"], "name": player_row["name"]},
        "total_matches": total_matches,
        "wins": wins,
        "losses": losses,
        "win_pct": win_pct,
    }


def get_surface_stats(player_name: str, surface: str) -> Dict[str, Any]:
    with get_connection() as conn:
        player_row = (
            conn.execute(
                text("SELECT player_id, name FROM players WHERE name = :name"),
                {"name": player_name},
            )
            .mappings()
            .fetchone()
        )
        if not player_row:
            return {
                "player": {"id": None, "name": player_name},
                "surface": surface,
                "total_matches": 0,
                "wins": 0,
                "losses": 0,
                "win_pct": 0.0,
            }

        total_matches_row = (
            conn.execute(
                text(
                    """
                    SELECT COUNT(*) AS total
                    FROM matches
                    WHERE (player1_id = :player_id OR player2_id = :player_id)
                      AND surface = :surface
                    """
                ),
                {"player_id": player_row["player_id"], "surface": surface},
            )
            .mappings()
            .fetchone()
        )
        wins_row = (
            conn.execute(
                text(
                    """
                    SELECT COUNT(*) AS wins
                    FROM matches
                    WHERE winner_id = :player_id
                      AND surface = :surface
                    """
                ),
                {"player_id": player_row["player_id"], "surface": surface},
            )
            .mappings()
            .fetchone()
        )

    total_matches = int(total_matches_row["total"]) if total_matches_row else 0
    wins = int(wins_row["wins"]) if wins_row else 0
    losses = max(total_matches - wins, 0)
    win_pct = round((wins / total_matches) * 100, 2) if total_matches else 0.0

    return {
        "player": {"id": player_row["player_id"], "name": player_row["name"]},
        "surface": surface,
        "total_matches": total_matches,
        "wins": wins,
        "losses": losses,
        "win_pct": win_pct,
    }

