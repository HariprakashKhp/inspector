"""Offline HTTP doubles and opt-in PostgreSQL tests in isolated schemas."""

from collections.abc import Callable, Iterator
from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from alembic import command
from alembic.config import Config
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import URL, create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.schema import CreateSchema, DropSchema

from app.database import get_database_url
from app.main import create_app
from app.models import Incident
from app.repositories import get_incident_repository, incident_response
from app.schemas import IncidentCreate, IncidentPage, IncidentResponse

Backend = tuple[FastAPI, Callable[[], dict[UUID, IncidentResponse]]]


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--postgres", action="store_true", help="Also run isolated PostgreSQL tests"
    )


class FakeIncidentRepository:
    """Only an HTTP test double; test database behavior against PostgreSQL."""

    def __init__(self) -> None:
        self.incidents: dict[UUID, IncidentResponse] = {}

    def create(self, incident: IncidentCreate) -> IncidentResponse:
        created = IncidentResponse(
            **incident.model_dump(), id=uuid4(), created_at=datetime.now(UTC)
        )
        self.incidents[created.id] = created
        return created

    def get(self, incident_id: UUID) -> IncidentResponse | None:
        return self.incidents.get(incident_id)

    def list(self, *, limit: int, offset: int) -> IncidentPage:
        ordered = sorted(
            self.incidents.values(),
            key=lambda incident: (incident.created_at, incident.id),
            reverse=True,
        )
        return IncidentPage(
            items=ordered[offset : offset + limit],
            limit=limit,
            offset=offset,
            has_more=len(ordered) > offset + limit,
        )


@pytest.fixture
def postgres_url(request: pytest.FixtureRequest) -> Iterator[URL]:
    if not request.config.getoption("--postgres"):
        pytest.skip("use --postgres with the configured local PostgreSQL server")
    admin_engine = create_engine(
        get_database_url(), connect_args={"connect_timeout": 5}
    )
    schema = f"inspector_test_{uuid4().hex}"
    with admin_engine.begin() as connection:
        connection.execute(CreateSchema(schema))
    url = get_database_url().update_query_dict({"options": f"-csearch_path={schema}"})
    engine = create_engine(url, connect_args={"connect_timeout": 5})
    try:
        with engine.begin() as connection:
            config = Config("alembic.ini")
            config.attributes["connection"] = connection
            command.upgrade(config, "head")
        yield url
    finally:
        engine.dispose()
        with admin_engine.begin() as connection:
            # Only the unique schema created by this fixture is removed.
            connection.execute(DropSchema(schema, cascade=True))
        admin_engine.dispose()


@pytest.fixture(params=["fake", "postgres"])
def incident_backend(request: pytest.FixtureRequest) -> Iterator[Backend]:
    if request.param == "fake":
        repository = FakeIncidentRepository()
        # The dependency override prevents connections to this unused engine.
        app = create_app("postgresql+psycopg://unused@127.0.0.1/unused")
        app.dependency_overrides[get_incident_repository] = lambda: repository
        yield app, lambda: repository.incidents.copy()
    else:
        url = request.getfixturevalue("postgres_url")
        engine = create_engine(url)

        def snapshot() -> dict[UUID, IncidentResponse]:
            with Session(engine) as session:
                return {
                    row.id: incident_response(row)
                    for row in session.scalars(select(Incident))
                }

        try:
            yield create_app(url), snapshot
        finally:
            engine.dispose()


@pytest.fixture
def client(incident_backend: Backend) -> Iterator[TestClient]:
    app, _ = incident_backend
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def stored_incidents(
    incident_backend: Backend,
) -> Callable[[], dict[UUID, IncidentResponse]]:
    _, snapshot = incident_backend
    return snapshot
