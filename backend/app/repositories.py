"""Commit incident writes and map stored rows to the API response contract."""

from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_session
from app.models import Incident
from app.schemas import IncidentCreate, IncidentPage, IncidentResponse


def incident_response(row: Incident) -> IncidentResponse:
    return IncidentResponse(
        id=row.id,
        service=row.service,
        severity=row.severity,
        summary=row.summary,
        created_at=row.created_at.astimezone(UTC),
    )


class IncidentRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, incident: IncidentCreate) -> IncidentResponse:
        row = Incident(
            **incident.model_dump(), id=uuid4(), created_at=datetime.now(UTC)
        )
        self.session.add(row)
        self.session.commit()
        return incident_response(row)

    def get(self, incident_id: UUID) -> IncidentResponse | None:
        row = self.session.get(Incident, incident_id)
        return incident_response(row) if row is not None else None

    def list(self, *, limit: int, offset: int) -> IncidentPage:
        rows = self.session.scalars(
            select(Incident)
            .order_by(Incident.created_at.desc(), Incident.id.desc())
            .limit(limit + 1)
            .offset(offset)
        ).all()
        return IncidentPage(
            items=[incident_response(row) for row in rows[:limit]],
            limit=limit,
            offset=offset,
            has_more=len(rows) > limit,
        )


def get_incident_repository(
    session: Annotated[Session, Depends(get_session)],
) -> IncidentRepository:
    return IncidentRepository(session)
