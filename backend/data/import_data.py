from pathlib import Path
import sqlite3
import subprocess

import pandas as pd


BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "tennis.db"
SCHEMA_PATH = BASE_DIR / "database" / "schema.sql"
DATA_DIR = BASE_DIR / "data" / "raw" / "atp"
DATA_VERSION_PATH = BASE_DIR / "data" / "DATA_VERSION.txt"


def setup_database() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        with open(SCHEMA_PATH, "r", encoding="utf-8") as schema_file:
            conn.executescript(schema_file.read())


def record_data_version() -> None:
    if not DATA_DIR.exists():
        return
    try:
        result = subprocess.run(
            ["git", "-C", str(DATA_DIR), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
        commit = result.stdout.strip()
        if commit:
            DATA_VERSION_PATH.write_text(f"{commit}\n", encoding="utf-8")
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass


def import_players() -> None:
    players_path = DATA_DIR / "atp_players.csv"
    if not players_path.exists():
        print(f"Missing {players_path}")
        return

    df = pd.read_csv(players_path, low_memory=False)
    df["name"] = (
        df["name_first"].fillna("").str.strip() + " " + df["name_last"].fillna("").str.strip()
    ).str.strip()
    df = df[["player_id", "name", "hand", "dob", "ioc"]].rename(
        columns={"dob": "birth_date", "ioc": "country"}
    )
    df["player_id"] = df["player_id"].astype(str)
    df = df.where(pd.notna(df), None)

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DELETE FROM players")
        df.to_sql("players", conn, if_exists="append", index=False)


def import_tournaments() -> None:
    match_files = sorted(DATA_DIR.glob("atp_matches_????.csv"))
    if not match_files:
        print(f"No match files found in {DATA_DIR}")
        return

    frames = []
    for file in match_files:
        frames.append(
            pd.read_csv(
                file,
                usecols=["tourney_id", "tourney_name", "tourney_level", "surface", "draw_size"],
                low_memory=False,
            )
        )
    df = pd.concat(frames, ignore_index=True).drop_duplicates(subset=["tourney_id"])
    df = df.rename(
        columns={
            "tourney_id": "tournament_id",
            "tourney_name": "name",
            "tourney_level": "level",
        }
    )
    df["tournament_id"] = df["tournament_id"].astype(str)
    df = df[["tournament_id", "name", "level", "surface", "draw_size"]]
    df = df.where(pd.notna(df), None)

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DELETE FROM tournaments")
        df.to_sql("tournaments", conn, if_exists="append", index=False)


def import_matches() -> None:
    match_files = sorted(DATA_DIR.glob("atp_matches_????.csv"))
    if not match_files:
        print(f"No match files found in {DATA_DIR}")
        return

    frames = []
    for file in match_files:
        header = pd.read_csv(file, nrows=0)
        required = {
            "tourney_id",
            "tourney_date",
            "surface",
            "round",
            "winner_id",
            "loser_id",
            "score",
            "minutes",
            "match_num",
        }
        if not required.issubset(header.columns):
            print(f"Skipping {file.name}: missing columns {sorted(required - set(header.columns))}")
            continue

        df = pd.read_csv(
            file,
            usecols=sorted(required),
            low_memory=False,
        )
        df["match_id"] = df["tourney_id"].astype(str) + "_" + df["match_num"].astype(str)
        df["tournament_id"] = df["tourney_id"].astype(str)
        df["date"] = df["tourney_date"].astype(str)
        df["player1_id"] = df["winner_id"].astype(str)
        df["player2_id"] = df["loser_id"].astype(str)
        df["winner_id"] = df["winner_id"].astype(str)
        df["minutes"] = pd.to_numeric(df["minutes"], errors="coerce").astype("Int64")
        df = df[
            [
                "match_id",
                "tournament_id",
                "date",
                "surface",
                "round",
                "player1_id",
                "player2_id",
                "winner_id",
                "score",
                "minutes",
            ]
        ]
        df = df.where(pd.notna(df), None)
        frames.append(df)

    merged = pd.concat(frames, ignore_index=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DELETE FROM matches")
        merged.to_sql("matches", conn, if_exists="append", index=False)


def import_rankings() -> None:
    ranking_files = sorted(DATA_DIR.glob("atp_rankings_*.csv"))
    if not ranking_files:
        print(f"No ranking files found in {DATA_DIR}")
        return

    frames = []
    for file in ranking_files:
        df = pd.read_csv(file, usecols=["ranking_date", "rank", "player", "points"])
        df = df.rename(
            columns={"ranking_date": "date", "player": "player_id"}
        )
        df["player_id"] = df["player_id"].astype(str)
        df["rank"] = pd.to_numeric(df["rank"], errors="coerce").astype("Int64")
        df["points"] = pd.to_numeric(df["points"], errors="coerce").astype("Int64")
        df = df.where(pd.notna(df), None)
        frames.append(df)

    merged = pd.concat(frames, ignore_index=True)
    merged = merged.dropna(subset=["player_id", "date"])
    merged = merged.drop_duplicates(subset=["player_id", "date"], keep="last")
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DELETE FROM rankings")
        merged.to_sql("rankings", conn, if_exists="append", index=False)


if __name__ == "__main__":
    setup_database()
    if DATA_DIR.exists():
        print("Importing players...")
        import_players()
        print("Importing tournaments...")
        import_tournaments()
        print("Importing matches...")
        import_matches()
        print("Importing rankings...")
        import_rankings()
    else:
        print(f"Data directory not found: {DATA_DIR}")
    record_data_version()
    print(f"Database ready at {DB_PATH}")

