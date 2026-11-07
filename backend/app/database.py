"""PostgreSQL configuration and a session scoped to each request."""

import os
from collections.abc import Iterator
from pathlib import Path

from dotenv import load_dotenv
from fastapi import Request
from sqlalchemy import URL
from sqlalchemy.orm import Session

ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


def get_database_url() -> URL:
    """Build a URL without putting credentials in source or log messages."""
    # Use the repository file regardless of the working directory. Shell/deployment
    # settings take priority, and utf-8-sig also accepts Windows UTF-8 BOM files.
    load_dotenv(ENV_FILE, override=False, encoding="utf-8-sig")
    password = os.getenv("PGPASSWORD")
    if not password:
        raise RuntimeError("Set PGPASSWORD before starting the API or migrations")
    try:
        port = int(os.getenv("PGPORT", "5433"))
    except ValueError:
        raise RuntimeError("PGPORT must be an integer between 1 and 65535") from None
    if not 1 <= port <= 65535:
        raise RuntimeError("PGPORT must be an integer between 1 and 65535")
    return URL.create(
        "postgresql+psycopg",
        username=os.getenv("PGUSER", "inspector"),
        password=password,
        host=os.getenv("PGHOST", "127.0.0.1"),
        port=port,
        database=os.getenv("PGDATABASE", "inspector"),
    )


def get_session(request: Request) -> Iterator[Session]:
    """Close each session, rolling back any unfinished transaction."""
    with request.app.state.session_factory() as session:
        yield session
