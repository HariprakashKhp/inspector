# Inspector

A learning project for an AI production incident investigator. The specification is in [Project.md](Project.md), shared contributor instructions are in [AGENTS.md](AGENTS.md), and the current learning task is in [LEARNING_TRACKER.md](LEARNING_TRACKER.md).

## Current Scope

Milestones 1 and 2 include PostgreSQL-backed incident create/get/list endpoints, SQLAlchemy, Alembic migrations, and a repeatable synthetic seed command. The existing create/get contract is unchanged. `GET /health` reports that the API is responding; it does not check database readiness. Investigation contracts and synthetic evidence follow in INV-01.

## Repository Layout

```text
compose.yaml          # Local PostgreSQL 17 with a persistent named volume
.env.example          # Local connection settings; copy to ignored .env
backend/
  .python-version     # Python 3.12.12
  pyproject.toml      # Runtime/development dependencies and tool settings
  uv.lock             # Resolved dependency versions; commit this file
  app/
    __init__.py
    main.py           # App factory, connection-pool lifecycle, HTTP endpoints
    database.py       # Environment configuration and request-scoped sessions
    models.py         # SQLAlchemy incident table mapping and constraints
    repositories.py   # Incident writes/reads and response mapping
    schemas.py        # Incident severity and request/response contracts
    seed.py           # Insert missing synthetic incidents with stable IDs
  alembic.ini         # Migration configuration; contains no credentials
  migrations/         # Environment and versioned schema changes
  tests/
    conftest.py        # Offline doubles and isolated PostgreSQL schemas
    test_health.py     # Health endpoint HTTP contract
    test_incidents.py  # Create/get contracts, offline and with PostgreSQL
    test_incident_list.py # List pagination, validation, ordering, and consistency
    test_seed.py       # Seed repeatability, preservation, and atomicity
    test_database.py   # Environment configuration checks
    test_persistence.py # Migrations, transactions, and app restart checks
    test_schemas.py    # Incident validation and serialization checks
```

`worker/`, `frontend/`, `infra/`, `evals/`, and `docs/` will be added as their milestones need them.

## Local Setup (PowerShell)

Prerequisites: Git, [uv](https://docs.astral.sh/uv/getting-started/installation/), Python 3.12.12, and Docker Desktop running Linux containers. `uv` can install the pinned Python version if it is missing. Initial setup requires network access to download dependencies and the PostgreSQL image. An existing local PostgreSQL server can also be used by configuring the same connection settings and omitting the Compose command.

Run from the repository root:

```powershell
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
# Before continuing, edit .env and replace the PGPASSWORD placeholder.
docker compose up -d --wait postgres

cd backend
uv sync --locked
uv run alembic upgrade head
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

`uv sync` creates `backend/.venv` and installs the locked runtime and development dependencies. `uv run` uses that environment without manual activation. Keep the server terminal open and use another terminal for requests; stop it with Ctrl+C.

Compose reads the repository-root `.env`. The API and Alembic also load that exact file automatically through `python-dotenv` in their shared database configuration; no `--env-file` flag is needed. The path is based on the source file location, so it does not depend on the terminal's working directory. Existing shell/deployment environment variables take priority over file values. Restart the API after changing `.env` to load the new settings.

The app and Alembic share `PGHOST`, `PGPORT`, `PGDATABASE`, `PGUSER`, and `PGPASSWORD`. Defaults are `127.0.0.1:5433`, database `inspector`, user `inspector`; the password is required and has no default. A missing `.env` is allowed when environment variables supply the configuration. SQLAlchemy builds the URL from these fields, so passwords containing URL punctuation do not need manual escaping. `.env` is ignored by Git; only the placeholder example is tracked.

The container exposes PostgreSQL only on loopback. `PGPORT` is its host port; the container still listens on 5432 internally. Run migrations before serving requests: application startup creates a connection pool, but never creates or migrates tables. Existing in-memory incidents from milestone 1 are not copied to PostgreSQL; submit the synthetic example again after this transition.

If API port 8000 is occupied, use another port such as `--port 8001` and update the request URLs below. If the database port is occupied, choose another `PGPORT` in `.env` before starting Compose. PostgreSQL initializes its database/user/password only for a new volume; changing `.env` does not change credentials already stored in that volume.

If the shared uv cache is inaccessible, set a local cache before running the commands:

```powershell
$env:UV_CACHE_DIR = "$PWD\.cache\uv"
```

## Try the API

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

Expected JSON: `{"status":"ok"}` with HTTP 200. Open <http://127.0.0.1:8000/docs> for interactive API documentation. No API keys are needed for this step.

Create a synthetic incident while the server is running:

```powershell
$incidentBody = @{
    service = "checkout-api"
    severity = "high"
    summary = "Latency increased after the latest deployment"
} | ConvertTo-Json

$createdIncident = Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/incidents `
    -ContentType "application/json" -Body $incidentBody

$createdIncident
```

The API returns HTTP 201 with the validated fields, a server-generated UUID `id`, and a UTC `created_at` timestamp. Invalid requests return HTTP 422, including unsupported severity or client-supplied `id`/`created_at` fields. Repeated submissions create separate incidents.

Retrieve the incident using the ID returned by POST:

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/incidents/$($createdIncident.id)"
```

For a readable JSON response and a quick comparison, capture the GET result:

```powershell
$retrievedIncident = Invoke-RestMethod -Uri "http://127.0.0.1:8000/incidents/$($createdIncident.id)"
$retrievedIncident | ConvertTo-Json

# Expected: no output, because every returned field matches the POST response.
Compare-Object -ReferenceObject @($createdIncident) -DifferenceObject @($retrievedIncident) `
    -Property service, severity, summary, id, created_at
```

Example response shape (the server generates a different ID and timestamp for each creation):

```json
{
  "service": "checkout-api",
  "severity": "high",
  "summary": "Latency increased after the latest deployment",
  "id": "5ef5c484-f6be-46bb-9a13-10de0f4e54af",
  "created_at": "2026-11-06T10:00:00Z"
}
```

`GET /incidents/{incident_id}` returns HTTP 200 with the same fields, ID, and timestamp returned by POST. A valid UUID that is not stored returns HTTP 404 with `{"detail":"Incident not found"}`. A malformed UUID returns HTTP 422: FastAPI validates the path before the handler runs.

Incidents are committed to PostgreSQL before POST returns HTTP 201. They survive API restarts and development reloads, and app processes connected to the same database read the same records. The named Docker volume retains database files when the container stops or is recreated.

To demonstrate persistence, keep the request terminal open so `$createdIncident` remains available. Stop the API server with Ctrl+C, start it again using the same startup command, and repeat the GET above: it still returns HTTP 200 with the original data. Milestone 1's in-memory version returned 404 after restart; PostgreSQL removes that limitation.

To inspect failure cases in `/docs`, expand a route, select **Try it out**, enter the input, and select **Execute**. For GET, use `not-a-uuid` to see HTTP 422, or generate a fresh UUID with `[guid]::NewGuid().ToString()` in PowerShell and use it to see HTTP 404. For POST, change the example severity to `urgent` to see HTTP 422. Inspect the response status and body; invalid requests do not create a record.

## List Incidents

`GET /incidents` returns HTTP 200 with an `IncidentPage` containing `items`, `limit`, `offset`, and `has_more`. Each item has the same fields and values as create/get. An empty database or an offset past the final record returns `items: []` and `has_more: false`.

| Parameter | Default | Accepted values |
|---|---|---|
| `limit` | 20 | Integer from 1 to 100 |
| `offset` | 0 | Nonnegative signed 64-bit integer |

Invalid query values return HTTP 422. Results are ordered by `created_at` descending (newest first), then `id` descending to break equal-timestamp ties. The database fetches at most `limit + 1` rows; the extra row indicates whether another page exists, and only `limit` rows are returned. There is no total-count query.

With the API running, use a second PowerShell terminal:

```powershell
$page = Invoke-RestMethod "http://127.0.0.1:8000/incidents?limit=2&offset=0"
$page | ConvertTo-Json -Depth 5

if ($page.has_more) {
    $nextOffset = $page.offset + $page.limit
    Invoke-RestMethod "http://127.0.0.1:8000/incidents?limit=2&offset=$nextOffset"
}
```

Ordering is deterministic for unchanged data. New incidents inserted between page requests can shift offset boundaries, so separate requests do not share a fixed snapshot. Large offsets also require skipping more rows; this initial pagination is intended for the local learning dataset.

## Seed Synthetic Incidents

Run from `backend/` with PostgreSQL available; the API server does not need to be running:

```powershell
uv run alembic upgrade head
uv run python -m app.seed
```

The command reads the same `.env` configuration as the API and inserts three synthetic incidents for checkout latency, payment errors, and inventory delays. On a database without those seed IDs, it prints:

```text
Inserted 3 synthetic incidents; skipped 0 existing IDs.
```

Running it again prints `Inserted 0 synthetic incidents; skipped 3 existing IDs.` The seed fixtures use deterministic UUID v5 IDs and fixed UTC timestamps on 2026-01-01. Normal POST requests still generate fresh UUID v4 IDs and the current UTC time. Seed records may appear after newer incidents in the list.

All seed inserts run in one transaction. PostgreSQL `ON CONFLICT (id) DO NOTHING` skips existing IDs, including overlapping runs; it does not overwrite edited seed records or unrelated incidents. The command inserts missing fixtures and does not reset the database. Missing tables or database failures stop the command with an error rather than reporting success. Retrieve the records through the API list/get endpoints or view `public.incidents` in pgAdmin.

## Development Checks

Run these from `backend/`:

```powershell
uv run python -m pytest
uv run ruff check .
uv run ruff format --check .

# Also run the HTTP contracts and persistence checks against local PostgreSQL.
uv run python -m pytest --postgres
uv run alembic current
uv run alembic check
```

The default test run uses a fake incident repository for HTTP validation and skips PostgreSQL cases. It does not prove persistence. `--postgres` also runs the create/get/list contracts against the actual repository, plus migration, restart/sharing, constraints, failed-commit recovery, timestamp-tie ordering, and seed repeatability/preservation/rollback checks. Each database test creates a randomly named `inspector_test_*` schema, migrates it, and drops only that schema afterward; the configured test user needs permission to create schemas. Tests leave the main incident table untouched. Use a local development database, never a production connection. Migration downgrade/upgrade is tested only inside the disposable test schema.

Use `uv run ruff format .` to apply formatting. When dependencies change, regenerate `uv.lock` with `uv lock` and commit it alongside `pyproject.toml`. The FastAPI [first steps](https://fastapi.tiangolo.com/tutorial/first-steps/) and [testing guide](https://fastapi.tiangolo.com/tutorial/testing/) explain the app and TestClient pattern.

## Request Flow and Persistence Review

Trace `GET /health`: Uvicorn imports the `app` object from `app.main`, FastAPI selects the registered route, and the handler returns a dictionary that becomes a JSON response. The test exercises that HTTP behavior in process, without starting a network server.

Review `backend/app/main.py` and its tests. Explain what `app.main:app` means, how `@app.get("/health")` connects a URL to a function, and what the test proves. Milestone 1 introduced validation and server-generated identity/time using temporary storage. DB-01 moves storage into an `IncidentRepository` backed by a request-scoped SQLAlchemy session.

The create/get flow fits together as follows:

1. **Routing:** Uvicorn passes the HTTP request to FastAPI. The HTTP method and URL select `create_incident` for POST or `get_incident` for GET.
2. **Validation:** POST parses the JSON body as `IncidentCreate`, trimming text, checking required fields and severity, and rejecting extra fields. GET parses `incident_id` as a UUID. Invalid input returns HTTP 422 before the handler runs.
3. **Identity and storage:** The repository calls `uuid4()` and `datetime.now(UTC)`, constructs an SQLAlchemy `Incident` row, adds it to the session, and commits. Only then does it return an `IncidentResponse`. Clients cannot supply `id` or `created_at` because these are not allowed request fields.
4. **Retrieval:** The repository looks up the parsed UUID with `session.get(Incident, incident_id)`. The handler returns the stored data with HTTP 200, or raises `HTTPException` with HTTP 404 if the row is missing. Retrieval preserves the original ID and creation time.
5. **Response:** `response_model=IncidentResponse` defines the output contract; FastAPI serializes the UUID and timestamp into JSON strings. A successful POST returns HTTP 201.

The Pydantic schemas validate HTTP input/output; the SQLAlchemy model maps stored columns; the Alembic migration creates the actual table, primary key, severity/length constraints, and timezone-aware timestamp column. Changes to the model do not update an existing database automatically. A session groups database work into a transaction. Closing each request's session releases its connection and rolls back unfinished work; a failed commit returns an error instead of HTTP 201. Synchronous database handlers run in FastAPI's thread pool, avoiding blocking the async event loop. App shutdown disposes its connection pool while committed rows remain in PostgreSQL.

See the [SQLAlchemy session guide](https://docs.sqlalchemy.org/en/20/orm/session_basics.html) and [Alembic tutorial](https://alembic.sqlalchemy.org/en/latest/tutorial.html) for the database mechanisms used here.

After trying the examples, explain these points in your own words:

- Why does `urgent` return 422 before anything is stored?
- Why does an unknown valid UUID return 404 while `not-a-uuid` returns 422?
- Where are `id` and `created_at` generated, and why does GET return the original values?
- Why did restarting lose incidents in milestone 1, and why do restart and multiple app processes now retain/share records?
- What is the difference between a Pydantic schema, a SQLAlchemy model, and an Alembic migration?
- Why must the commit succeed before POST returns 201, and what happens to unfinished work when a session closes?
- Why does listing order by both creation time and UUID, and why does it fetch one extra row?
- Why does running the seed command twice preserve existing rows instead of creating duplicates?

Automated HTTP tests exercise the app in process; the PowerShell demonstration also checks Uvicorn and real network requests. The next implementation task after DB-02 is INV-01: define investigation contracts and the checkout-latency evidence scenario. No investigation or LLM execution is implemented yet.

## Database Lifecycle and Rollback

From the repository root, `docker compose stop postgres` stops the local database while preserving data. Resume with `docker compose up -d --wait postgres`. `docker compose down` removes this project's containers/network and retains the named volume. Do not add `--volumes` unless you intend to delete the database files.

Alembic revision `0001` creates the incident table. `alembic upgrade head` is safe to repeat after it succeeds. Take a backup before any rollback involving data. `uv run alembic downgrade base` (from `backend/`) explicitly drops the incident table and all its records; it is destructive, and is not part of normal startup. Stopping the API/database preserves records and is sufficient when pausing development. Reverting to the old in-memory application does not import PostgreSQL rows or preserve any new in-memory submissions; the database can be kept intact while diagnosing a problem.

## Incident Data Contract

`backend/app/schemas.py` defines the shape of incident data. These are Pydantic API schemas, not database models. The incident creation endpoint uses them to validate requests and serialize responses.

| Schema | Fields | Who supplies them? |
|---|---|---|
| `IncidentCreate` | `service`, `severity`, `summary` | Client submitting the incident |
| `IncidentResponse` | The same fields plus `id` and `created_at` | Server returning the incident |
| `IncidentPage` | `items` (incident responses), `limit`, `offset`, `has_more` | Server returning a list page |

- `service`: required string, 1–100 characters after trimming surrounding whitespace.
- `summary`: required string, 1–1,000 characters after trimming surrounding whitespace.
- `severity`: exactly `low`, `medium`, `high`, or `critical`, chosen by the reporter.
- Unexpected request fields, including client-supplied `id` or `created_at`, are rejected.
- Response `id` is a UUID; `created_at` must include timezone information. The schemas validate these fields; the creation endpoint generates a UUID v4 and UTC timestamp.

`IncidentResponse` inherits the three shared fields and their validation from `IncidentCreate`. Pydantic checks data when a model is constructed and raises `ValidationError` for invalid data. See the [field constraint documentation](https://docs.pydantic.dev/latest/concepts/fields/) for the validation mechanism.

Try this from `backend/` without needing an HTTP endpoint:

```powershell
uv run python -c "from app.schemas import IncidentCreate; print(IncidentCreate(service='checkout-api', severity='high', summary='Latency spike').model_dump_json())"
```

Change `high` to `urgent` to see a validation error. FastAPI applies the same schema validation to incoming incident requests before the handler runs. Current schema tests check supported and unsupported severity, whitespace, length boundaries, required fields, unexpected fields, and response serialization/timezone handling. HTTP tests also verify successful creation/storage, UTC timestamps, distinct IDs, trimmed text, and rejection without storage changes.
