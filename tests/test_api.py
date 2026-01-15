from fastapi.testclient import TestClient

from backend.main import app


client = TestClient(app)


def test_health_endpoint():
    # Sanity check for API liveness and DB connection.
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"ok": True}


def test_players_endpoint():
    # Ensure the players endpoint returns a list container.
    response = client.get("/api/players?limit=3")
    assert response.status_code == 200
    payload = response.json()
    assert "players" in payload
    assert isinstance(payload["players"], list)
    assert len(payload["players"]) <= 3


def test_player_detail_endpoint():
    # Fetch a known player by ID (Federer).
    response = client.get("/api/players/103819")
    assert response.status_code == 200
    payload = response.json()
    assert payload["player_id"] == "103819"
    assert payload["name"] == "Roger Federer"


def test_player_detail_not_found():
    # Unknown player IDs should return a 404.
    response = client.get("/api/players/000000")
    assert response.status_code == 404
    payload = response.json()
    assert payload["detail"] == "Player not found"


def test_player_matches_endpoint():
    # Fetch match history with pagination and filters.
    response = client.get("/api/players/103819/matches?limit=5&year=2017")
    assert response.status_code == 200
    payload = response.json()
    assert payload["player_id"] == "103819"
    assert payload["total_matches"] >= 1
    assert len(payload["matches"]) <= 5


def test_query_unknown_type():
    # Unrecognized queries should return a consistent 400 error response.
    response = client.post("/api/query", json={"query": "What is the meaning of life?"})
    assert response.status_code == 400
    payload = response.json()
    assert payload["detail"]["error"] == "Unable to determine query type"


def test_query_missing_player():
    # Query type detected but player not recognized.
    response = client.post("/api/query", json={"query": "Grand Slam wins"})
    assert response.status_code == 400
    payload = response.json()
    assert payload["detail"]["error"] == "Player not recognized"


def test_query_endpoint():
    # Basic parser integration: route accepts input and returns parsed intent.
    response = client.post("/api/query", json={"query": "Federer Grand Slam wins"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["query"] == "Federer Grand Slam wins"
    assert payload["parsed"]["type"] == "grand_slam_titles"
    assert payload["results"] is not None
    assert payload["results"]["count"] >= 1


def test_query_head_to_head():
    # Head-to-head queries return aggregated wins and match list.
    response = client.post("/api/query", json={"query": "Federer vs Nadal"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["parsed"]["type"] == "head_to_head"
    assert payload["results"]["player1"]["wins"] + payload["results"]["player2"]["wins"] >= 1


def test_query_tournament_winner():
    # Tournament winner queries return a list of winners for the year.
    response = client.post("/api/query", json={"query": "Who won Wimbledon 2019?"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["parsed"]["type"] == "tournament_winner"
    assert payload["results"]["count"] >= 1


def test_query_career_stats():
    # Career stats return win/loss totals for the player.
    response = client.post("/api/query", json={"query": "Djokovic career wins"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["parsed"]["type"] == "career_stats"
    assert payload["results"]["total_matches"] >= 1


def test_query_surface_stats():
    # Surface stats return win/loss totals for the player on a surface.
    response = client.post("/api/query", json={"query": "Nadal clay court record"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["parsed"]["type"] == "surface_stats"
    assert payload["results"]["total_matches"] >= 1
