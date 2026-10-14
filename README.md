# Inspector

A learning project for an AI production incident investigator. The specification is in [Project.md](Project.md), shared contributor instructions are in [AGENTS.md](AGENTS.md), and the current learning task is in [LEARNING_TRACKER.md](LEARNING_TRACKER.md).

## Current Scope

Milestone 1 includes a minimal FastAPI backend with `GET /health` and validated incident request/response schemas. Incident creation and retrieval endpoints are the next steps. The endpoint reports that the API is responding; database and external-service readiness checks will follow when those dependencies exist.

## Repository Layout

```text
backend/
  .python-version     # Python 3.12.12
  pyproject.toml      # Runtime/development dependencies and tool settings
  uv.lock             # Resolved dependency versions; commit this file
  app/
    __init__.py
    main.py           # FastAPI app and health endpoint
    schemas.py        # Incident severity and request/response contracts
  tests/
    test_health.py     # Health endpoint HTTP contract test
    test_schemas.py    # Incident validation and serialization checks
```

`worker/`, `frontend/`, `infra/`, `evals/`, and `docs/` will be added as their milestones need them.

## Local Setup (PowerShell)

Prerequisites: Git, [uv](https://docs.astral.sh/uv/getting-started/installation/), and Python 3.12.12. `uv` can install the pinned Python version if it is missing. Initial setup requires network access to download dependencies.

Run from the repository root:

```powershell
cd backend
uv sync --locked
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

`uv sync` creates `backend/.venv` and installs the locked runtime and development dependencies. `uv run` uses that environment without manual activation. Keep the server terminal open and use another terminal for requests; stop it with Ctrl+C.

If the shared uv cache is inaccessible, set a local cache before running the commands:

```powershell
$env:UV_CACHE_DIR = "$PWD\.cache\uv"
```

## Try the API

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

Expected JSON: `{"status":"ok"}` with HTTP 200. Open <http://127.0.0.1:8000/docs> for interactive API documentation. No API keys are needed for this step.

## Development Checks

Run these from `backend/`:

```powershell
uv run python -m pytest
uv run ruff check .
uv run ruff format --check .
```

Use `uv run ruff format .` to apply formatting. When dependencies change, regenerate `uv.lock` with `uv lock` and commit it alongside `pyproject.toml`. The FastAPI [first steps](https://fastapi.tiangolo.com/tutorial/first-steps/) and [testing guide](https://fastapi.tiangolo.com/tutorial/testing/) explain the app and TestClient pattern.

## First Learning Review

Trace `GET /health`: Uvicorn imports the `app` object from `app.main`, FastAPI selects the registered route, and the handler returns a dictionary that becomes a JSON response. The test exercises that HTTP behavior in process, without starting a network server.

Review `backend/app/main.py` and its test. Explain what `app.main:app` means, how `@app.get("/health")` connects a URL to a function, and what the test proves. Next, review the incident data contract below; the following coding step adds `POST /incidents`.

## Incident Data Contract

`backend/app/schemas.py` defines the shape of incident data. These are Pydantic API schemas, not database models. They will be connected to FastAPI endpoints in the next step.

| Schema | Fields | Who supplies them? |
|---|---|---|
| `IncidentCreate` | `service`, `severity`, `summary` | Client submitting the incident |
| `IncidentResponse` | The same fields plus `id` and `created_at` | Server returning the incident |

- `service`: required string, 1–100 characters after trimming surrounding whitespace.
- `summary`: required string, 1–1,000 characters after trimming surrounding whitespace.
- `severity`: exactly `low`, `medium`, `high`, or `critical`, chosen by the reporter.
- Unexpected request fields, including client-supplied `id` or `created_at`, are rejected.
- Response `id` is a UUID; `created_at` must include timezone information. The schemas validate these fields; the endpoint will generate them later.

`IncidentResponse` inherits the three shared fields and their validation from `IncidentCreate`. Pydantic checks data when a model is constructed and raises `ValidationError` for invalid data. See the [field constraint documentation](https://docs.pydantic.dev/latest/concepts/fields/) for the validation mechanism.

Try this from `backend/` without needing an HTTP endpoint:

```powershell
uv run python -c "from app.schemas import IncidentCreate; print(IncidentCreate(service='checkout-api', severity='high', summary='Latency spike').model_dump_json())"
```

Change `high` to `urgent` to see a validation error. When these schemas are attached to an endpoint, FastAPI can validate incoming requests before the handler runs. Current schema tests check supported and unsupported severity, whitespace, length boundaries, required fields, unexpected fields, and response serialization/timezone handling.
