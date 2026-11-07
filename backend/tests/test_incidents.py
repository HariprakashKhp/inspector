"""Unchanged HTTP contracts, run offline and optionally against PostgreSQL."""

from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from app.schemas import IncidentResponse


@pytest.fixture
def incident_payload() -> dict[str, str]:
    return {
        "service": "checkout-api",
        "severity": "high",
        "summary": "Latency increased after the latest deployment",
    }


def test_create_returns_and_stores_incident(
    client: TestClient,
    incident_payload: dict[str, str],
    stored_incidents: Callable[[], dict[UUID, IncidentResponse]],
) -> None:
    before = datetime.now(UTC)
    response = client.post("/incidents", json=incident_payload)
    after = datetime.now(UTC)

    assert response.status_code == 201
    created = IncidentResponse.model_validate(response.json())
    assert created.model_dump(mode="json", exclude={"id", "created_at"}) == (
        incident_payload
    )
    assert created.id.version == 4
    assert before <= created.created_at <= after
    assert created.created_at.utcoffset() == timedelta(0)
    assert stored_incidents() == {created.id: created}


def test_create_trims_text(
    client: TestClient, incident_payload: dict[str, str]
) -> None:
    incident_payload.update(service="  checkout-api  ", summary="  Latency spike  ")

    response = client.post("/incidents", json=incident_payload)

    assert response.status_code == 201
    assert response.json()["service"] == "checkout-api"
    assert response.json()["summary"] == "Latency spike"


def test_repeated_requests_create_distinct_incidents(
    client: TestClient,
    incident_payload: dict[str, str],
    stored_incidents: Callable[[], dict[UUID, IncidentResponse]],
) -> None:
    first = client.post("/incidents", json=incident_payload)
    second = client.post("/incidents", json=incident_payload)

    assert first.status_code == second.status_code == 201
    first_id = UUID(first.json()["id"])
    second_id = UUID(second.json()["id"])
    assert first_id != second_id
    assert set(stored_incidents()) == {first_id, second_id}


@pytest.mark.parametrize(
    "field, value",
    [
        ("severity", "urgent"),
        ("service", "   "),
        ("id", "5ef5c484-f6be-46bb-9a13-10de0f4e54af"),
        ("created_at", "2026-11-06T10:00:00Z"),
    ],
)
def test_invalid_create_does_not_store_incident(
    client: TestClient,
    incident_payload: dict[str, str],
    field: str,
    value: str,
    stored_incidents: Callable[[], dict[UUID, IncidentResponse]],
) -> None:
    incident_payload[field] = value

    response = client.post("/incidents", json=incident_payload)

    assert response.status_code == 422
    assert any(error["loc"] == ["body", field] for error in response.json()["detail"])
    assert stored_incidents() == {}


def test_create_requires_summary(
    client: TestClient,
    incident_payload: dict[str, str],
    stored_incidents: Callable[[], dict[UUID, IncidentResponse]],
) -> None:
    del incident_payload["summary"]

    response = client.post("/incidents", json=incident_payload)

    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["body", "summary"]
    assert stored_incidents() == {}


def test_get_returns_the_requested_incident(
    client: TestClient, incident_payload: dict[str, str]
) -> None:
    first = client.post("/incidents", json=incident_payload)
    second = client.post(
        "/incidents", json={**incident_payload, "service": "payments-api"}
    )
    assert first.status_code == second.status_code == 201

    for created in (first.json(), second.json()):
        response = client.get(f"/incidents/{created['id']}")

        assert response.status_code == 200
        assert response.json() == created


def test_get_unknown_uuid_returns_not_found(
    client: TestClient, incident_payload: dict[str, str]
) -> None:
    created = client.post("/incidents", json=incident_payload)
    assert created.status_code == 201

    response = client.get("/incidents/5ef5c484-f6be-46bb-9a13-10de0f4e54af")

    assert response.status_code == 404
    assert response.json() == {"detail": "Incident not found"}
    stored = client.get(f"/incidents/{created.json()['id']}")
    assert stored.status_code == 200
    assert stored.json() == created.json()


def test_get_malformed_uuid_returns_validation_error(client: TestClient) -> None:
    response = client.get("/incidents/not-a-uuid")

    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["path", "incident_id"]
