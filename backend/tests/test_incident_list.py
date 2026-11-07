"""Pagination contracts run with both offline doubles and real PostgreSQL."""

from datetime import UTC, datetime
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import URL, create_engine
from sqlalchemy.orm import Session

from app.main import create_app
from app.models import Incident


def test_list_empty_database_returns_default_page(client: TestClient) -> None:
    response = client.get("/incidents")
    assert response.status_code == 200
    assert response.json() == {
        "items": [],
        "limit": 20,
        "offset": 0,
        "has_more": False,
    }


def test_create_get_and_paginated_list_are_consistent(client: TestClient) -> None:
    created = []
    for service in ("checkout-api", "payments-api", "inventory-api"):
        response = client.post(
            "/incidents",
            json={
                "service": service,
                "severity": "high",
                "summary": "Synthetic latency",
            },
        )
        assert response.status_code == 201
        created.append(response.json())
    expected = sorted(
        created,
        key=lambda row: (datetime.fromisoformat(row["created_at"]), UUID(row["id"])),
        reverse=True,
    )
    first = client.get("/incidents?limit=2&offset=0")
    assert first.status_code == 200
    assert first.json() == {
        "items": expected[:2],
        "limit": 2,
        "offset": 0,
        "has_more": True,
    }
    assert client.get("/incidents?limit=2&offset=0").json() == first.json()
    last = client.get("/incidents?limit=2&offset=2")
    assert last.status_code == 200
    assert last.json() == {
        "items": expected[2:],
        "limit": 2,
        "offset": 2,
        "has_more": False,
    }
    exact = client.get("/incidents?limit=3")
    assert exact.json() == {
        "items": expected,
        "limit": 3,
        "offset": 0,
        "has_more": False,
    }
    for item in first.json()["items"] + last.json()["items"]:
        retrieved = client.get(f"/incidents/{item['id']}")
        assert retrieved.status_code == 200
        assert retrieved.json() == item
    beyond = client.get("/incidents?limit=2&offset=999")
    assert beyond.status_code == 200
    assert beyond.json() == {
        "items": [],
        "limit": 2,
        "offset": 999,
        "has_more": False,
    }


@pytest.mark.parametrize("limit", [1, 100])
def test_list_accepts_page_size_boundaries(client: TestClient, limit: int) -> None:
    response = client.get("/incidents", params={"limit": limit, "offset": 50})
    assert response.status_code == 200
    assert response.json() == {
        "items": [],
        "limit": limit,
        "offset": 50,
        "has_more": False,
    }


@pytest.mark.parametrize(
    "field,value",
    [
        ("limit", "0"),
        ("limit", "-1"),
        ("limit", "101"),
        ("limit", "abc"),
        ("limit", "1.5"),
        ("offset", "-1"),
        ("offset", "abc"),
        ("offset", "1.5"),
        ("offset", str(2**63)),
    ],
)
def test_invalid_pagination_returns_422(
    client: TestClient, field: str, value: str
) -> None:
    response = client.get("/incidents", params={field: value})
    assert response.status_code == 422
    assert any(error["loc"] == ["query", field] for error in response.json()["detail"])


def test_postgres_list_uses_uuid_to_break_equal_timestamp_ties(
    postgres_url: URL,
) -> None:
    engine = create_engine(postgres_url)
    try:
        with Session(engine) as session, session.begin():
            for value, minute in ((1, 0), (3, 0), (2, 0), (0, 1)):
                session.add(
                    Incident(
                        id=UUID(int=value),
                        service="checkout-api",
                        severity="high",
                        summary=f"Synthetic incident {value}",
                        created_at=datetime(2026, 1, 1, 10, minute, tzinfo=UTC),
                    )
                )
        with TestClient(create_app(postgres_url)) as client:
            first = client.get("/incidents?limit=2")
            second = client.get("/incidents?limit=2&offset=2")
            assert first.status_code == second.status_code == 200
            assert [row["id"] for row in first.json()["items"]] == [
                str(UUID(int=0)),
                str(UUID(int=3)),
            ]
            assert [row["id"] for row in second.json()["items"]] == [
                str(UUID(int=2)),
                str(UUID(int=1)),
            ]
            assert first.json()["has_more"] is True
            assert second.json()["has_more"] is False
    finally:
        engine.dispose()
