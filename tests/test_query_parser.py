from backend.api.query_parser import parse_natural_query


def test_parse_returns_structure():
    # Detects a grand slam query and maps a known player name.
    result = parse_natural_query("Federer Grand Slam wins")
    assert result["raw"] == "Federer Grand Slam wins"
    assert result["type"] == "grand_slam_titles"
    assert result["player"] == "Roger Federer"
    assert result["opponent"] is None


def test_parse_surface_and_year():
    # Extracts surface + year filters from the query text.
    result = parse_natural_query("Nadal clay court wins 2013")
    assert result["filters"]["surface"] == "Clay"
    assert result["filters"]["year"] == "2013"


def test_parse_tournament_winner():
    # Extracts tournament and year for winner queries.
    result = parse_natural_query("Who won Wimbledon 2019?")
    assert result["type"] == "tournament_winner"
    assert result["filters"]["tournament"] == "Wimbledon"
    assert result["filters"]["year"] == "2019"


def test_parse_career_stats():
    # Detects a career stats query.
    result = parse_natural_query("Djokovic career wins")
    assert result["type"] == "career_stats"
    assert result["player"] == "Novak Djokovic"


def test_parse_surface_stats():
    # Detects surface-specific stats intent.
    result = parse_natural_query("Nadal clay court record")
    assert result["type"] == "surface_stats"
    assert result["player"] == "Rafael Nadal"
    assert result["filters"]["surface"] == "Clay"

