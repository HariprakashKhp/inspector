"""Incident HTTP contracts, separate from database table mappings."""

from enum import StrEnum
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field


class IncidentSeverity(StrEnum):
    """Supported severity labels supplied by the incident reporter."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IncidentCreate(BaseModel):
    """Client-supplied fields for a new incident."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    service: str = Field(min_length=1, max_length=100)
    severity: IncidentSeverity
    summary: str = Field(min_length=1, max_length=1000)


class IncidentResponse(IncidentCreate):
    """Incident fields plus identity and creation time supplied by the server."""

    id: UUID
    created_at: AwareDatetime


class IncidentPage(BaseModel):
    """A bounded page; has_more is determined by fetching one extra row."""

    items: list[IncidentResponse]
    limit: int
    offset: int
    has_more: bool
