"""Repeatable synthetic incidents: run `uv run python -m app.seed` from backend/."""

from datetime import UTC, datetime
from uuid import NAMESPACE_URL, uuid5

from sqlalchemy import create_engine
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.database import get_database_url
from app.models import Incident
from app.schemas import IncidentResponse

SEED_INCIDENTS = (
    IncidentResponse(
        id=uuid5(NAMESPACE_URL, "inspector:seed:v1:checkout-latency"),
        service="checkout-api",
        severity="high",
        summary="Synthetic demo: checkout latency increased after a deployment",
        created_at=datetime(2026, 1, 1, 10, 0, tzinfo=UTC),
    ),
    IncidentResponse(
        id=uuid5(NAMESPACE_URL, "inspector:seed:v1:payment-errors"),
        service="payments-api",
        severity="critical",
        summary="Synthetic demo: payment requests return elevated errors",
        created_at=datetime(2026, 1, 1, 10, 1, tzinfo=UTC),
    ),
    IncidentResponse(
        id=uuid5(NAMESPACE_URL, "inspector:seed:v1:inventory-delay"),
        service="inventory-api",
        severity="medium",
        summary="Synthetic demo: inventory updates are delayed",
        created_at=datetime(2026, 1, 1, 10, 2, tzinfo=UTC),
    ),
)


def seed_incidents(session: Session) -> int:
    """Insert missing stable IDs; the caller owns the transaction/commit."""
    statement = (
        insert(Incident)
        .values([incident.model_dump() for incident in SEED_INCIDENTS])
        .on_conflict_do_nothing(index_elements=[Incident.id])
        .returning(Incident.id)
    )
    return len(session.scalars(statement).all())


def main() -> None:
    engine = create_engine(
        get_database_url(), hide_parameters=True, connect_args={"connect_timeout": 5}
    )
    try:
        with Session(engine) as session, session.begin():
            inserted = seed_incidents(session)
    finally:
        engine.dispose()
    print(
        f"Inserted {inserted} synthetic incidents; "
        f"skipped {len(SEED_INCIDENTS) - inserted} existing IDs."
    )


if __name__ == "__main__":
    main()
