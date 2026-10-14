"""Validation and serialization checks for incident data contracts."""

from datetime import UTC, datetime
from uuid import UUID

import pytest
from pydantic import ValidationError

from app.schemas import IncidentCreate, IncidentResponse, IncidentSeverity


@pytest.fixture
def incident_payload() -> dict[str, str]:
    return {
        "service": "checkout-api",
        "severity": "high",
        "summary": "Latency increased after the latest deployment",
    }


@pytest.mark.parametrize("severity", ["low", "medium", "high", "critical"])
def test_create_accepts_supported_severity(
    incident_payload: dict[str, str], severity: str
) -> None:
    incident_payload["severity"] = severity

    incident = IncidentCreate.model_validate(incident_payload)

    assert incident.severity == IncidentSeverity(severity)
    assert incident.model_dump(mode="json") == incident_payload


def test_create_trims_service_and_summary(incident_payload: dict[str, str]) -> None:
    incident_payload.update(service="  checkout-api  ", summary="  Latency spike  ")

    incident = IncidentCreate.model_validate(incident_payload)

    assert incident.service == "checkout-api"
    assert incident.summary == "Latency spike"


@pytest.mark.parametrize("severity", ["urgent", "HIGH"])
def test_create_rejects_unsupported_severity(
    incident_payload: dict[str, str], severity: str
) -> None:
    incident_payload["severity"] = severity

    with pytest.raises(ValidationError) as caught:
        IncidentCreate.model_validate(incident_payload)

    assert caught.value.errors()[0]["loc"] == ("severity",)


@pytest.mark.parametrize("field", ["service", "summary"])
@pytest.mark.parametrize("value", ["", "   "])
def test_create_rejects_blank_text(
    incident_payload: dict[str, str], field: str, value: str
) -> None:
    incident_payload[field] = value

    with pytest.raises(ValidationError) as caught:
        IncidentCreate.model_validate(incident_payload)

    assert caught.value.errors()[0]["loc"] == (field,)


@pytest.mark.parametrize("field, limit", [("service", 100), ("summary", 1000)])
def test_create_enforces_text_length_limits(
    incident_payload: dict[str, str], field: str, limit: int
) -> None:
    incident_payload[field] = "a" * limit
    IncidentCreate.model_validate(incident_payload)
    incident_payload[field] += "a"

    with pytest.raises(ValidationError) as caught:
        IncidentCreate.model_validate(incident_payload)

    assert caught.value.errors()[0]["loc"] == (field,)


@pytest.mark.parametrize("field", ["service", "severity", "summary"])
def test_create_requires_all_fields(
    incident_payload: dict[str, str], field: str
) -> None:
    del incident_payload[field]

    with pytest.raises(ValidationError) as caught:
        IncidentCreate.model_validate(incident_payload)

    assert caught.value.errors()[0]["loc"] == (field,)


@pytest.mark.parametrize("field", ["id", "created_at", "unknown_field"])
def test_create_rejects_unexpected_fields(
    incident_payload: dict[str, str], field: str
) -> None:
    incident_payload[field] = "client-supplied-value"

    with pytest.raises(ValidationError) as caught:
        IncidentCreate.model_validate(incident_payload)

    assert caught.value.errors()[0]["type"] == "extra_forbidden"


def test_response_serializes_identity_and_timestamp(
    incident_payload: dict[str, str],
) -> None:
    incident_id = UUID("5ef5c484-f6be-46bb-9a13-10de0f4e54af")
    created_at = datetime(2026, 10, 14, 10, 0, tzinfo=UTC)
    response = IncidentResponse(
        **incident_payload, id=incident_id, created_at=created_at
    )

    serialized = response.model_dump(mode="json")

    assert serialized == {
        **incident_payload,
        "id": str(incident_id),
        "created_at": "2026-10-14T10:00:00Z",
    }
    assert IncidentResponse.model_validate_json(response.model_dump_json()) == response


def test_response_rejects_naive_timestamp(incident_payload: dict[str, str]) -> None:
    with pytest.raises(ValidationError) as caught:
        IncidentResponse(
            **incident_payload,
            id=UUID("5ef5c484-f6be-46bb-9a13-10de0f4e54af"),
            created_at=datetime(2026, 10, 14, 10, 0),
        )

    assert caught.value.errors()[0]["loc"] == ("created_at",)
