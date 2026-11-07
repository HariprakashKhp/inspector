"""Real PostgreSQL migrations, transactions, and app lifecycle verification."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from fastapi.testclient import TestClient
from sqlalchemy import URL, create_engine, func, inspect, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.main import create_app
from app.models import Base, Incident

PAYLOAD = {
    "service": "checkout-api",
    "severity": "high",
    "summary": "Latency increased after the latest deployment",
}


def test_migration_matches_models_and_can_be_repeated(postgres_url: URL) -> None:
    engine = create_engine(postgres_url)
    try:
        with engine.begin() as connection:
            assert set(inspect(connection).get_table_names()) == {
                "incidents",
                "alembic_version",
            }
            assert connection.scalar(
                text("SELECT version_num FROM alembic_version")
            ) == ("0001")
            config = Config("alembic.ini")
            config.attributes["connection"] = connection
            command.upgrade(config, "head")
            context = MigrationContext.configure(connection)
            assert compare_metadata(context, Base.metadata) == []
            # Rollback is exercised only in this fixture's empty temporary schema.
            command.downgrade(config, "base")
            assert inspect(connection).get_table_names() == ["alembic_version"]
            command.upgrade(config, "head")
            assert compare_metadata(context, Base.metadata) == []
    finally:
        engine.dispose()


def test_incident_survives_new_app_and_is_shared_between_apps(
    postgres_url: URL,
) -> None:
    with TestClient(create_app(postgres_url)) as first:
        created = first.post("/incidents", json=PAYLOAD)
        assert created.status_code == 201
        incident = created.json()
        path = f"/incidents/{incident['id']}"
        with TestClient(create_app(postgres_url)) as second:
            shared = second.get(path)
            assert shared.status_code == 200
            assert shared.json() == incident
    # Both original lifespans and connection pools have been closed.
    with TestClient(create_app(postgres_url)) as restarted:
        retrieved = restarted.get(path)
        assert retrieved.status_code == 200
        assert retrieved.json() == incident


def test_database_rejects_invalid_severity(
    postgres_url: URL,
) -> None:
    engine = create_engine(postgres_url)
    try:
        with Session(engine) as session:
            session.add(
                Incident(
                    **{**PAYLOAD, "severity": "urgent"},
                    id=uuid4(),
                    created_at=datetime.now(UTC),
                )
            )
            with pytest.raises(IntegrityError):
                session.commit()
            session.rollback()
            assert session.scalar(select(func.count()).select_from(Incident)) == 0
    finally:
        engine.dispose()


def test_failed_commit_returns_500_and_next_request_can_commit(
    postgres_url: URL, monkeypatch: pytest.MonkeyPatch
) -> None:
    first_id, next_id = uuid4(), uuid4()
    ids = iter([first_id, first_id, next_id])
    monkeypatch.setattr("app.repositories.uuid4", lambda: next(ids))
    with TestClient(create_app(postgres_url), raise_server_exceptions=False) as client:
        first = client.post("/incidents", json=PAYLOAD)
        assert first.status_code == 201
        failed = client.post("/incidents", json=PAYLOAD)
        assert failed.status_code == 500
        assert failed.text == "Internal Server Error"
        third = client.post("/incidents", json=PAYLOAD)
        assert third.status_code == 201
        assert third.json()["id"] == str(next_id)
        assert client.get(f"/incidents/{first_id}").json() == first.json()
    engine = create_engine(postgres_url)
    try:
        with Session(engine) as session:
            assert session.scalar(select(func.count()).select_from(Incident)) == 2
    finally:
        engine.dispose()
