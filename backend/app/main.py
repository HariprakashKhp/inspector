"""FastAPI entry point for the Inspector backend."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Annotated
from uuid import UUID

from fastapi import Depends, FastAPI, HTTPException, Query, status
from sqlalchemy import URL, create_engine
from sqlalchemy.orm import sessionmaker

from app.database import get_database_url
from app.repositories import IncidentRepository, get_incident_repository
from app.schemas import IncidentCreate, IncidentPage, IncidentResponse

Repository = Annotated[IncidentRepository, Depends(get_incident_repository)]


def create_app(database_url: str | URL | None = None) -> FastAPI:
    """Build the API; migrations are run explicitly before serving requests."""

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
        engine = create_engine(
            database_url if database_url is not None else get_database_url(),
            pool_pre_ping=True,
            hide_parameters=True,
            connect_args={"connect_timeout": 5},
        )
        app.state.session_factory = sessionmaker(engine, expire_on_commit=False)
        try:
            yield
        finally:
            engine.dispose()

    app = FastAPI(
        title="Inspector API",
        description="AI incident investigation learning project",
        version="0.1.0",
        lifespan=lifespan,
    )

    @app.get("/health", tags=["health"])
    async def health() -> dict[str, str]:
        """Confirm the API is responding; dependency readiness comes later."""
        return {"status": "ok"}

    @app.post(
        "/incidents",
        response_model=IncidentResponse,
        status_code=status.HTTP_201_CREATED,
        tags=["incidents"],
    )
    def create_incident(
        incident: IncidentCreate, repository: Repository
    ) -> IncidentResponse:
        """Generate identity/time and return only after the database commits."""
        return repository.create(incident)

    @app.get("/incidents", response_model=IncidentPage, tags=["incidents"])
    def list_incidents(
        repository: Repository,
        limit: Annotated[int, Query(ge=1, le=100)] = 20,
        offset: Annotated[int, Query(ge=0, le=2**63 - 1)] = 0,
    ) -> IncidentPage:
        """List newest incidents first, using UUID descending to break time ties."""
        return repository.list(limit=limit, offset=offset)

    @app.get(
        "/incidents/{incident_id}", response_model=IncidentResponse, tags=["incidents"]
    )
    def get_incident(incident_id: UUID, repository: Repository) -> IncidentResponse:
        """Return a stored incident, or 404 if its UUID is unknown."""
        incident = repository.get(incident_id)
        if incident is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found"
            )
        return incident

    return app


app = create_app()
