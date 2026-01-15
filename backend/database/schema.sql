CREATE TABLE IF NOT EXISTS players (
    player_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    hand TEXT,
    birth_date TEXT,
    country TEXT
);

CREATE TABLE IF NOT EXISTS matches (
    match_id TEXT PRIMARY KEY,
    tournament_id TEXT,
    date TEXT,
    surface TEXT,
    round TEXT,
    player1_id TEXT,
    player2_id TEXT,
    winner_id TEXT,
    score TEXT,
    minutes INTEGER,
    FOREIGN KEY (player1_id) REFERENCES players(player_id),
    FOREIGN KEY (player2_id) REFERENCES players(player_id),
    FOREIGN KEY (winner_id) REFERENCES players(player_id)
);

CREATE INDEX IF NOT EXISTS idx_matches_player1 ON matches(player1_id);
CREATE INDEX IF NOT EXISTS idx_matches_player2 ON matches(player2_id);
CREATE INDEX IF NOT EXISTS idx_matches_winner ON matches(winner_id);
CREATE INDEX IF NOT EXISTS idx_matches_date ON matches(date);
CREATE INDEX IF NOT EXISTS idx_matches_surface ON matches(surface);

CREATE TABLE IF NOT EXISTS tournaments (
    tournament_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    level TEXT,
    surface TEXT,
    draw_size INTEGER
);

CREATE TABLE IF NOT EXISTS rankings (
    player_id TEXT,
    date TEXT,
    rank INTEGER,
    points INTEGER,
    PRIMARY KEY (player_id, date),
    FOREIGN KEY (player_id) REFERENCES players(player_id)
);

CREATE INDEX IF NOT EXISTS idx_rankings_date ON rankings(date);
CREATE INDEX IF NOT EXISTS idx_rankings_rank ON rankings(rank);

