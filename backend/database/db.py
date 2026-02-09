from pathlib import Path
import os
from urllib.parse import urlparse

from sqlalchemy import create_engine
from sqlalchemy.engine import Connection, Engine

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "tennis.db"
_ENGINE: Engine | None = None


def get_database_url() -> str:
    if "DATABASE_URL" in os.environ:
        return os.environ["DATABASE_URL"]
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{DB_PATH}"


def get_engine() -> Engine:
    global _ENGINE
    if _ENGINE is None:
        database_url = get_database_url()
        connect_args = {}
        if database_url.startswith("sqlite:///"):
            connect_args = {"check_same_thread": False}
        elif database_url.startswith(("postgresql://", "postgres://")):
            parsed = urlparse(database_url)
            # Supabase transaction pooler (port 6543) does not support prepared statements
            if parsed.port == 6543:
                connect_args = {"prepare_threshold": 0}
        _ENGINE = create_engine(database_url, future=True, connect_args=connect_args)
    return _ENGINE


def get_connection() -> Connection:
    return get_engine().connect()

