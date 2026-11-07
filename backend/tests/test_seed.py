"""Repeatable seed writes verified against isolated PostgreSQL schemas."""

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import URL, create_engine, func, select
from sqlalchemy.orm import Session

from app import seed
from app.main import create_app
from app.models import Incident


def test_seed_command_repeats_without_duplicates_and_matches_get_list(
    postgres_url: URL,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(seed, "get_database_url", lambda: postgres_url)
    seed.main()
    assert capsys.readouterr().out == (
        "Inserted 3 synthetic incidents; skipped 0 existing IDs.\n"
    )
    seed.main()
    assert capsys.readouterr().out == (
        "Inserted 0 synthetic incidents; skipped 3 existing IDs.\n"
    )
    expected = [row.model_dump(mode="json") for row in reversed(seed.SEED_INCIDENTS)]
    with TestClient(create_app(postgres_url)) as client:
        response = client.get("/incidents")
        assert response.status_code == 200
        assert response.json() == {
            "items": expected,
            "limit": 20,
            "offset": 0,
            "has_more": False,
        }
        for item in expected:
            retrieved = client.get(f"/incidents/{item['id']}")
            assert retrieved.status_code == 200
            assert retrieved.json() == item


def test_seed_preserves_existing_records_and_inserts_only_missing_ids(
    postgres_url: URL,
) -> None:
    engine = create_engine(postgres_url)
    edited = seed.SEED_INCIDENTS[0].model_copy(update={"summary": "Edited locally"})
    unrelated = seed.SEED_INCIDENTS[1].model_copy(
        update={
            "id": uuid4(),
            "summary": "Unrelated synthetic record",
        }
    )
    try:
        with Session(engine) as session, session.begin():
            session.add_all(
                [
                    Incident(**edited.model_dump()),
                    Incident(**unrelated.model_dump()),
                ]
            )
        with Session(engine) as session, session.begin():
            assert seed.seed_incidents(session) == 2
        with Session(engine) as session:
            assert session.scalar(select(func.count()).select_from(Incident)) == 4
            assert session.get(Incident, edited.id).summary == edited.summary
            assert session.get(Incident, unrelated.id).summary == unrelated.summary
    finally:
        engine.dispose()


def test_seed_respects_transaction_rollback(postgres_url: URL) -> None:
    engine = create_engine(postgres_url)
    try:
        with pytest.raises(RuntimeError, match="Synthetic failure"):
            with Session(engine) as session, session.begin():
                assert seed.seed_incidents(session) == 3
                raise RuntimeError("Synthetic failure")
        with Session(engine) as session:
            assert session.scalar(select(func.count()).select_from(Incident)) == 0
    finally:
        engine.dispose()
