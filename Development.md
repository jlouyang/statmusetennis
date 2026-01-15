# Tennis Stats Platform - Development Guide

## Project Context
This is a StatMuse-style tennis statistics platform with natural language search capabilities. The goal is to allow users to query tennis stats using plain English (e.g., "Show me Federer's Grand Slam wins on clay").

---

## Architecture Overview

### Tech Stack
- **Backend**: Python + FastAPI
- **Database**: SQLite (local file-based)
- **Data Source**: Jeff Sackmann's tennis datasets (CSV files)
- **NLP**: Simple pattern matching initially, LLM integration later
- **Frontend**: React (to be added later)

### System Design
```
User Query → API Layer → Query Parser → Database → Results
```

---

## Project Structure

```
tennis-stats/
├── backend/
│   ├── main.py                 # FastAPI application entry point
│   ├── requirements.txt        # Python dependencies
│   │
│   ├── database/
│   │   ├── __init__.py
│   │   ├── db.py              # Database connection management
│   │   ├── schema.sql         # Database schema definition
│   │   ├── models.py          # SQLAlchemy ORM models (optional)
│   │   └── queries.py         # Reusable database queries
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes.py          # API endpoint definitions
│   │   └── query_parser.py    # Natural language query parsing
│   │
│   └── data/
│       ├── raw/               # Original CSV files from Sackmann
│       │   ├── atp_players.csv
│       │   ├── atp_matches_2024.csv
│       │   └── ...
│       ├── tennis.db          # SQLite database (generated)
│       └── import_data.py     # Script to import CSVs into SQLite
│
├── frontend/                   # To be added later
└── README.md
```

---

## Database Schema

### Core Tables

#### players
Stores player biographical information.
```sql
CREATE TABLE players (
    player_id TEXT PRIMARY KEY,      -- Unique identifier
    name TEXT NOT NULL,              -- Full name
    hand TEXT,                       -- R/L/U (right/left/unknown)
    birth_date TEXT,                 -- YYYYMMDD format
    country TEXT                     -- IOC country code
);
```

#### matches
Stores individual match results.
```sql
CREATE TABLE matches (
    match_id TEXT PRIMARY KEY,
    tournament_id TEXT,
    date TEXT,                       -- YYYYMMDD format
    surface TEXT,                    -- Hard/Clay/Grass/Carpet
    round TEXT,                      -- R128/R64/R32/R16/QF/SF/F
    player1_id TEXT,
    player2_id TEXT,
    winner_id TEXT,                  -- References player_id
    score TEXT,                      -- Match score string
    minutes INTEGER,                 -- Match duration
    FOREIGN KEY (player1_id) REFERENCES players(player_id),
    FOREIGN KEY (player2_id) REFERENCES players(player_id),
    FOREIGN KEY (winner_id) REFERENCES players(player_id)
);

-- Performance indexes
CREATE INDEX idx_matches_player1 ON matches(player1_id);
CREATE INDEX idx_matches_player2 ON matches(player2_id);
CREATE INDEX idx_matches_winner ON matches(winner_id);
CREATE INDEX idx_matches_date ON matches(date);
CREATE INDEX idx_matches_surface ON matches(surface);
```

#### tournaments
Stores tournament metadata.
```sql
CREATE TABLE tournaments (
    tournament_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    level TEXT,                      -- G/M/A/D (Grand Slam/Masters/ATP/Davis Cup)
    surface TEXT,
    draw_size INTEGER
);
```

#### rankings
Stores ATP/WTA ranking snapshots.
```sql
CREATE TABLE rankings (
    player_id TEXT,
    date TEXT,                       -- YYYYMMDD format
    rank INTEGER,
    points INTEGER,
    PRIMARY KEY (player_id, date),
    FOREIGN KEY (player_id) REFERENCES players(player_id)
);

CREATE INDEX idx_rankings_date ON rankings(date);
CREATE INDEX idx_rankings_rank ON rankings(rank);
```

---

## API Endpoints

### POST /api/query
Main natural language search endpoint.

**Request:**
```json
{
  "query": "How many Grand Slams has Federer won?"
}
```

**Response:**
```json
{
  "query": "How many Grand Slams has Federer won?",
  "parsed": {
    "type": "grand_slam_titles",
    "player": "Roger Federer",
    "filters": {}
  },
  "results": {
    "count": 20,
    "titles": [
      {
        "tournament": "Wimbledon",
        "date": "20170716",
        "opponent": "Marin Cilic",
        "score": "6-3 6-1 6-4"
      }
    ]
  }
}
```

### GET /api/players/{player_id}
Get player details.

**Response:**
```json
{
  "player_id": "103819",
  "name": "Roger Federer",
  "hand": "R",
  "birth_date": "19810808",
  "country": "SUI"
}
```

### GET /api/players/{player_id}/matches
Get player's match history with optional filters.

**Query Parameters:**
- `year`: Filter by year (e.g., 2023)
- `surface`: Filter by surface (hard/clay/grass)
- `tournament_level`: Filter by level (G/M/A)

**Response:**
```json
{
  "player_id": "103819",
  "player_name": "Roger Federer",
  "matches": [
    {
      "date": "20230115",
      "tournament": "Australian Open",
      "opponent": "Rafael Nadal",
      "result": "W",
      "score": "6-4 6-3 6-2"
    }
  ],
  "total_matches": 150
}
```

### GET /api/head-to-head/{player1_id}/{player2_id}
Get head-to-head statistics between two players.

**Response:**
```json
{
  "player1": {
    "id": "103819",
    "name": "Roger Federer",
    "wins": 16
  },
  "player2": {
    "id": "104745",
    "name": "Rafael Nadal",
    "wins": 24
  },
  "matches": [...],
  "by_surface": {
    "hard": {"player1_wins": 11, "player2_wins": 9},
    "clay": {"player1_wins": 2, "player2_wins": 14},
    "grass": {"player1_wins": 3, "player2_wins": 1}
  }
}
```

---

## Query Parser

### Supported Query Types (MVP)

1. **Grand Slam Titles**
   - "How many Grand Slams has Federer won?"
   - "Federer Grand Slam wins"
   - "Show me Nadal's majors"

2. **Head-to-Head**
   - "Federer vs Nadal"
   - "Head to head between Djokovic and Murray"
   - "Federer Nadal record"

3. **Surface-Specific Stats**
   - "Nadal clay court wins"
   - "Federer on grass"
   - "Djokovic hard court record"

4. **Tournament Results**
   - "Who won Wimbledon 2023?"
   - "Australian Open winners"
   - "French Open champions"

5. **Career Stats**
   - "Federer career wins"
   - "Nadal total titles"
   - "Djokovic win percentage"

### Parser Implementation Strategy

**Phase 1: Pattern Matching**
Use simple keyword detection and regex patterns.

```python
def parse_natural_query(query: str) -> dict:
    """
    Extract intent and entities from natural language query.
    Returns structured query parameters.
    """
    query_lower = query.lower()
    
    result = {
        "type": None,
        "player": None,
        "opponent": None,
        "filters": {}
    }
    
    # Detect players (expand this list)
    PLAYERS = {
        "federer": "Roger Federer",
        "nadal": "Rafael Nadal",
        "djokovic": "Novak Djokovic",
        "murray": "Andy Murray",
        # Add more as needed
    }
    
    for key, name in PLAYERS.items():
        if key in query_lower:
            if result["player"] is None:
                result["player"] = name
            else:
                result["opponent"] = name
    
    # Detect query type
    if any(term in query_lower for term in ["grand slam", "major", "majors"]):
        result["type"] = "grand_slam_titles"
    elif any(term in query_lower for term in ["vs", "versus", "head to head", "h2h"]):
        result["type"] = "head_to_head"
    elif "won" in query_lower and any(t in query_lower for t in ["wimbledon", "australian", "french", "us open"]):
        result["type"] = "tournament_winner"
    
    # Detect surface filters
    if "clay" in query_lower:
        result["filters"]["surface"] = "Clay"
    elif "grass" in query_lower:
        result["filters"]["surface"] = "Grass"
    elif "hard" in query_lower:
        result["filters"]["surface"] = "Hard"
    
    # Detect year filters
    import re
    year_match = re.search(r'\b(19|20)\d{2}\b', query_lower)
    if year_match:
        result["filters"]["year"] = year_match.group()
    
    return result
```

**Phase 2: LLM Integration** (Later)
Replace pattern matching with Claude/GPT API calls for better understanding.

---

## Database Queries Reference

### Common Query Patterns

#### Get Grand Slam Titles for a Player
```python
def get_grand_slam_titles(player_name: str, surface: str = None):
    """
    Get all Grand Slam titles won by a player.
    Optionally filter by surface.
    """
    query = """
    SELECT 
        t.name as tournament,
        m.date,
        m.score,
        p2.name as opponent
    FROM matches m
    JOIN players p1 ON (m.player1_id = p1.player_id OR m.player2_id = p1.player_id)
    JOIN players p2 ON (m.player1_id = p2.player_id OR m.player2_id = p2.player_id)
    JOIN tournaments t ON m.tournament_id = t.tournament_id
    WHERE p1.name = ?
        AND m.winner_id = p1.player_id
        AND p2.player_id != p1.player_id
        AND t.level = 'G'
        AND m.round = 'F'
    """
    
    params = [player_name]
    
    if surface:
        query += " AND m.surface = ?"
        params.append(surface)
    
    query += " ORDER BY m.date"
    
    # Execute and return results
```

#### Get Head-to-Head Record
```python
def get_head_to_head(player1_name: str, player2_name: str):
    """
    Get complete head-to-head record between two players.
    """
    query = """
    SELECT 
        m.date,
        t.name as tournament,
        m.surface,
        m.round,
        m.winner_id,
        m.score
    FROM matches m
    JOIN players p1 ON (m.player1_id = p1.player_id OR m.player2_id = p1.player_id)
    JOIN players p2 ON (m.player1_id = p2.player_id OR m.player2_id = p2.player_id)
    JOIN tournaments t ON m.tournament_id = t.tournament_id
    WHERE p1.name = ?
        AND p2.name = ?
        AND p1.player_id != p2.player_id
    ORDER BY m.date DESC
    """
    # Execute and calculate wins for each player
```

#### Get Player Statistics by Surface
```python
def get_player_stats_by_surface(player_name: str):
    """
    Get win/loss record broken down by surface.
    """
    query = """
    SELECT 
        m.surface,
        COUNT(*) as total_matches,
        SUM(CASE WHEN m.winner_id = p.player_id THEN 1 ELSE 0 END) as wins,
        SUM(CASE WHEN m.winner_id != p.player_id THEN 1 ELSE 0 END) as losses
    FROM matches m
    JOIN players p ON (m.player1_id = p.player_id OR m.player2_id = p.player_id)
    WHERE p.name = ?
    GROUP BY m.surface
    """
    # Execute and calculate win percentages
```

---

## Data Import Process

### Step 1: Download Sackmann Data
```bash
# Clone the repository
git clone https://github.com/JeffSackmann/tennis_atp.git data/raw/atp

# For WTA data
git clone https://github.com/JeffSackmann/tennis_wta.git data/raw/wta
```

### Step 2: Import Script Structure
```python
# data/import_data.py

import pandas as pd
import sqlite3
from pathlib import Path
import glob

def setup_database():
    """Create database and tables from schema.sql"""
    conn = sqlite3.connect('data/tennis.db')
    with open('database/schema.sql', 'r') as f:
        conn.executescript(f.read())
    conn.close()

def import_players():
    """Import player data"""
    conn = sqlite3.connect('data/tennis.db')
    
    # ATP players
    atp_players = pd.read_csv('data/raw/atp/atp_players.csv')
    atp_players.to_sql('players', conn, if_exists='append', index=False)
    
    conn.close()

def import_matches():
    """Import all match data"""
    conn = sqlite3.connect('data/tennis.db')
    
    # Get all match CSV files
    match_files = glob.glob('data/raw/atp/atp_matches_*.csv')
    
    for file in match_files:
        print(f"Importing {file}...")
        df = pd.read_csv(file)
        
        # Add match_id if not present
        if 'match_id' not in df.columns:
            df['match_id'] = df.index.astype(str) + '_' + Path(file).stem
        
        df.to_sql('matches', conn, if_exists='append', index=False)
    
    conn.close()

def import_rankings():
    """Import ranking data"""
    conn = sqlite3.connect('data/tennis.db')
    
    ranking_files = glob.glob('data/raw/atp/atp_rankings_*.csv')
    
    for file in ranking_files:
        df = pd.read_csv(file)
        df.to_sql('rankings', conn, if_exists='append', index=False)
    
    conn.close()

if __name__ == "__main__":
    print("Setting up database...")
    setup_database()
    
    print("Importing players...")
    import_players()
    
    print("Importing matches...")
    import_matches()
    
    print("Importing rankings...")
    import_rankings()
    
    print("Import complete!")
```

---

## Development Workflow

### Initial Setup
```bash
# 1. Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Download data
git clone https://github.com/JeffSackmann/tennis_atp.git backend/data/raw/atp

# 4. Import data into database
cd backend
python data/import_data.py

# 5. Run the API server
uvicorn main:app --reload
```

### Testing Workflow
```bash
# Test with curl
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Federer Grand Slam wins"}'

# Test specific endpoints
curl http://localhost:8000/api/players/103819
```

### Development Priorities

**Week 1: Data Foundation**
- [ ] Set up project structure
- [ ] Create database schema
- [ ] Import Sackmann data
- [ ] Verify data integrity

**Week 2: Basic API**
- [ ] Set up FastAPI application
- [ ] Implement database connection
- [ ] Create basic query functions
- [ ] Test with simple queries

**Week 3: Query Parser**
- [ ] Implement pattern matching parser
- [ ] Handle 5 basic query types
- [ ] Test with various phrasings
- [ ] Add error handling

**Week 4: API Endpoints**
- [ ] Implement all core endpoints
- [ ] Add query validation
- [ ] Implement pagination
- [ ] Add comprehensive error handling

---

## Code Style Guidelines

### Python
- Follow PEP 8
- Use type hints where appropriate
- Document functions with docstrings
- Keep functions focused and small
- Use meaningful variable names

### SQL
- Use uppercase for SQL keywords
- Indent subqueries
- Use meaningful aliases
- Always add indexes for foreign keys

### Error Handling
```python
# Always handle potential errors
try:
    result = query_database(sql, params)
    if not result:
        return {"error": "No results found"}
    return result
except sqlite3.Error as e:
    return {"error": f"Database error: {str(e)}"}
except Exception as e:
    return {"error": f"Unexpected error: {str(e)}"}
```

---

## Testing Strategy

### Unit Tests
Test individual functions in isolation.

```python
# tests/test_query_parser.py
def test_parse_grand_slam_query():
    result = parse_natural_query("Federer Grand Slam wins")
    assert result["type"] == "grand_slam_titles"
    assert result["player"] == "Roger Federer"

def test_parse_head_to_head():
    result = parse_natural_query("Federer vs Nadal")
    assert result["type"] == "head_to_head"
    assert result["player"] == "Roger Federer"
    assert result["opponent"] == "Rafael Nadal"
```

### Integration Tests
Test API endpoints end-to-end.

```python
# tests/test_api.py
from fastapi.testclient import TestClient

def test_query_endpoint():
    client = TestClient(app)
    response = client.post(
        "/api/query",
        json={"query": "Federer Grand Slam wins"}
    )
    assert response.status_code == 200
    assert "results" in response.json()
```

---

## Common Issues & Solutions

### Issue: Data import fails
**Solution**: Check CSV file encoding and delimiter. Sackmann uses UTF-8 and commas.

### Issue: Player name not recognized
**Solution**: Add to player lookup dictionary or implement fuzzy matching.

### Issue: Slow queries
**Solution**: 
- Add indexes to frequently queried columns
- Use EXPLAIN QUERY PLAN to identify bottlenecks
- Consider materialized views for complex aggregations

### Issue: Ambiguous queries
**Solution**: Return multiple interpretations and ask user to clarify.

---

## Next Steps After MVP

1. **Add LLM Integration**: Replace pattern matching with Claude/GPT API
2. **Implement Caching**: Add Redis for frequently accessed queries
3. **Add More Query Types**: Expand beyond the basic 5 types
4. **Build Frontend**: Create React interface
5. **Add Real-time Data**: Integrate live match scores
6. **User Accounts**: Save favorite players and queries
7. **Analytics**: Track popular queries to improve parser

---

## Resources

### Documentation
- FastAPI: https://fastapi.tiangolo.com
- SQLite: https://sqlite.org/docs.html
- Pandas: https://pandas.pydata.org/docs
- Sackmann Data Dictionary: Check README in tennis_atp repo

### Useful Queries for Testing
```
"How many Grand Slams has Federer won?"
"Federer vs Nadal head to head"
"Nadal clay court record"
"Who won Wimbledon 2019?"
"Djokovic career wins"
"Murray on grass"
```

---

## Contact & Feedback

When developing, focus on:
1. **Data quality**: Ensure accurate imports
2. **Query accuracy**: Results must be correct
3. **Response speed**: Queries should be fast (<500ms)
4. **Error handling**: Graceful failures with helpful messages
5. **Code clarity**: Other developers should understand your code