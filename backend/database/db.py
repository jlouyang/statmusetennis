from pathlib import Path
import os
from urllib.parse import urlparse

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Connection, Engine

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "tennis.db"
_ENGINE: Engine | None = None


def _set_psycopg2_no_prepare(connection: Connection, _branch: bool) -> None:
    """Disable server-side prepared statements (required for Supabase transaction pooler)."""
    connection.connection.prepare_threshold = 0  # type: ignore[union-attr]


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
        _ENGINE = create_engine(database_url, future=True, connect_args=connect_args)
        if database_url.startswith(("postgresql://", "postgres://")):
            parsed = urlparse(database_url)
            if parsed.port == 6543:
                event.listen(_ENGINE, "connect", _set_psycopg2_no_prepare)
    return _ENGINE


def get_connection() -> Connection:
    return get_engine().connect()

