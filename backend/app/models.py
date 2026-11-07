"""Database rows; the separate Pydantic schemas define the HTTP contract."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, String, Uuid
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Incident(Base):
    __tablename__ = "incidents"
    __table_args__ = (
        CheckConstraint(
            "severity IN ('low', 'medium', 'high', 'critical')",
            name="ck_incidents_severity",
        ),
        CheckConstraint(
            "char_length(trim(service)) BETWEEN 1 AND 100",
            name="ck_incidents_service_length",
        ),
        CheckConstraint(
            "char_length(trim(summary)) BETWEEN 1 AND 1000",
            name="ck_incidents_summary_length",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    service: Mapped[str] = mapped_column(String(100))
    severity: Mapped[str] = mapped_column(String(8))
    summary: Mapped[str] = mapped_column(String(1000))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
