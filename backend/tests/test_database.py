"""PostgreSQL configuration validation without requiring a running database."""

from pathlib import Path

import pytest

from app import database
from app.database import get_database_url


@pytest.fixture(autouse=True)
def isolated_environment(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Never load developer credentials or leave file-loaded values in other tests."""
    monkeypatch.setattr(database, "ENV_FILE", tmp_path / ".env")
    for name in (
        "PGHOST",
        "PGPORT",
        "PGDATABASE",
        "PGUSER",
        "PGPASSWORD",
        "PYTHON_DOTENV_DISABLED",
    ):
        # Register absent keys too, so teardown removes values load_dotenv sets.
        monkeypatch.setenv(name, "")
        monkeypatch.delenv(name)


def test_database_password_is_required(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("PGPASSWORD", raising=False)
    with pytest.raises(RuntimeError, match="Set PGPASSWORD"):
        get_database_url()


@pytest.mark.parametrize("port", ["not-a-port", "0", "65536"])
def test_invalid_port_is_rejected(monkeypatch: pytest.MonkeyPatch, port: str) -> None:
    monkeypatch.setenv("PGPASSWORD", "synthetic-test-password")
    monkeypatch.setenv("PGPORT", port)
    with pytest.raises(RuntimeError, match="PGPORT must be"):
        get_database_url()


def test_password_with_url_characters_is_preserved(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    password = "synthetic:p@ss/word%with#characters"
    for key, value in {
        "PGPASSWORD": password,
        "PGHOST": "127.0.0.1",
        "PGPORT": "5433",
        "PGDATABASE": "inspector",
        "PGUSER": "inspector",
    }.items():
        monkeypatch.setenv(key, value)
    url = get_database_url()
    assert url.password == password
    assert url.drivername == "postgresql+psycopg"
    assert password not in str(url)


def test_loads_database_settings_from_dotenv() -> None:
    database.ENV_FILE.write_text(
        "PGHOST=database.local\nPGPORT=5434\nPGDATABASE=synthetic_db\n"
        "PGUSER=synthetic_user\nPGPASSWORD='synthetic:p@ss/word%with#characters'\n",
        encoding="utf-8-sig",
    )
    url = get_database_url()
    assert (url.host, url.port, url.database, url.username, url.password) == (
        "database.local",
        5434,
        "synthetic_db",
        "synthetic_user",
        "synthetic:p@ss/word%with#characters",
    )


def test_environment_settings_override_dotenv(monkeypatch: pytest.MonkeyPatch) -> None:
    database.ENV_FILE.write_text(
        "PGHOST=file.local\nPGPORT=5434\nPGDATABASE=file_db\n"
        "PGUSER=file_user\nPGPASSWORD=file_password\n",
        encoding="utf-8",
    )
    for name, value in {
        "PGHOST": "environment.local",
        "PGPORT": "5435",
        "PGDATABASE": "environment_db",
        "PGUSER": "environment_user",
        "PGPASSWORD": "environment_password",
    }.items():
        monkeypatch.setenv(name, value)
    url = get_database_url()
    assert (url.host, url.port, url.database, url.username, url.password) == (
        "environment.local",
        5435,
        "environment_db",
        "environment_user",
        "environment_password",
    )


def test_dotenv_path_is_independent_of_working_directory(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    database.ENV_FILE.write_text("PGPASSWORD=repository_password\n", encoding="utf-8")
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    (elsewhere / ".env").write_text("PGPASSWORD=wrong_password\n", encoding="utf-8")
    monkeypatch.chdir(elsewhere)
    assert get_database_url().password == "repository_password"
