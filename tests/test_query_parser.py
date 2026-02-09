from backend.api.query_parser import parse_natural_query


def test_llm_parser_mock_grand_slams(monkeypatch):
    # LLM mock returns a structured response.
    monkeypatch.setenv("QUERY_PARSER", "llm")
    monkeypatch.setenv(
        "LLM_PARSER_MOCK",
        '{"type":"grand_slam_titles","player":"Roger Federer","opponent":null,"filters":{}}',
    )
    result = parse_natural_query("Federer Grand Slam wins")
    assert result["raw"] == "Federer Grand Slam wins"
    assert result["type"] == "grand_slam_titles"
    assert result["player"] == "Roger Federer"
    assert result["opponent"] is None
    assert result["filters"] == {}


def test_llm_parser_mock_tournament_winner(monkeypatch):
    # LLM mock returns tournament + year filters.
    monkeypatch.setenv("QUERY_PARSER", "llm")
    monkeypatch.setenv(
        "LLM_PARSER_MOCK",
        '{"type":"tournament_winner","player":null,"filters":{"tournament":"Wimbledon","year":"2019"}}',
    )
    result = parse_natural_query("Who won Wimbledon 2019?")
    assert result["type"] == "tournament_winner"
    assert result["filters"]["tournament"] == "Wimbledon"
    assert result["filters"]["year"] == "2019"


def test_llm_parser_mock_surface_stats(monkeypatch):
    # LLM mock returns surface stats intent.
    monkeypatch.setenv("QUERY_PARSER", "llm")
    monkeypatch.setenv(
        "LLM_PARSER_MOCK",
        '{"type":"surface_stats","player":"Rafael Nadal","filters":{"surface":"Clay"}}',
    )
    result = parse_natural_query("Nadal clay court record")
    assert result["type"] == "surface_stats"
    assert result["player"] == "Rafael Nadal"
    assert result["filters"]["surface"] == "Clay"


def test_llm_parser_invalid_mock(monkeypatch):
    # Invalid LLM output should fall back to rule-based parsing.
    monkeypatch.setenv("QUERY_PARSER", "llm")
    monkeypatch.setenv("LLM_PARSER_MOCK", '{"type":"unknown_type","filters":{"foo":"bar"}}')
    result = parse_natural_query("Federer Grand Slam wins")
    assert result["type"] == "grand_slam_titles"
    assert result["player"] is None


def test_rule_based_surface_and_year(monkeypatch):
    # Rule-based parser still extracts surface + year.
    monkeypatch.setenv("QUERY_PARSER", "rules")
    result = parse_natural_query("Nadal clay court wins 2013")
    assert result["filters"]["surface"] == "Clay"
    assert result["filters"]["year"] == "2013"


def test_llm_parser_fallback(monkeypatch):
    # LLM parser falls back when no API key is configured.
    monkeypatch.setenv("QUERY_PARSER", "llm")
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    monkeypatch.delenv("LLM_PARSER_MOCK", raising=False)
    result = parse_natural_query("Federer Grand Slam wins")
    assert result["type"] == "grand_slam_titles"
    assert result["player"] is None

