# Learning & Progress Tracker

## Purpose

Build the incident investigator in `Project.md` through small, working milestones. This is a learning project: understand the design, implement it, debug it, and demonstrate the result. The 12-week schedule is a rough guide; progress depends on working outcomes and understanding.

## How We Work

1. Explain one concept and why this project needs it.
2. Define a small task and its acceptance criteria.
3. Let the learner implement and ask questions; provide hints, examples, or direct help as needed.
4. Run the relevant checks and review both behavior and understanding.
5. Record the result, lessons, open questions, and next task here.

Keep work focused on the current milestone unless the user requests otherwise. Distinguish implemented behavior, verified behavior, and planned work. Record actual evidence before marking tasks complete.

## Current Position

- Current milestone: 3 — Investigation (next; not started).
- Status: milestones 1 and 2 complete; PostgreSQL create/get/list, pagination, and repeatable synthetic seeding verified. INV-01 is next.
- Existing artifacts: backend create/get/list API and schemas, SQLAlchemy models/repository, Alembic migration, PostgreSQL Compose configuration, synthetic seed command, tests, locked dependencies, and setup/review documentation. Local credentials live only in ignored `.env`.
- Next task: INV-01 — define investigation contracts and the checkout-latency synthetic evidence scenario.
- Task list: **API-01**, **API-02**, **API-03**, **DB-01**, and **DB-02** are complete. **INV-01** is next. Investigation execution and later tasks remain planned.
- Setup decisions: Python 3.12.12, uv, PostgreSQL 17 on loopback port 5433, synchronous SQLAlchemy 2 sessions with Psycopg 3, and explicit Alembic migrations. API/Alembic automatically load the repository-root `.env` using python-dotenv; existing environment variables take priority. Milestone 1 accepted by the learner on 2026-11-06.

## Milestone Roadmap

| Milestone | Working outcome | Main learning | Status |
|---|---|---|---|
| 1. Incident API | Submit and retrieve a synthetic incident | FastAPI, schemas, validation, HTTP, tests | Complete |
| 2. Persistence | Incidents survive an application restart | PostgreSQL, migrations, transactions | Complete |
| 3. Investigation | Synthetic evidence produces a structured report | Evidence adapters, LLM output, uncertainty | Planned |
| 4. Retrieval and evaluation | Reports cite relevant runbooks; quality is measured | RAG, labeled datasets, evaluation | Planned |
| 5. Reliability and delivery | Jobs recover from failures; approved sandbox actions are audited | Queues, retries, idempotency, security, observability, deployment | Planned |

Break later milestones into smaller tasks when reached. Add the dashboard after the incident-to-report backend works; expand infrastructure when the working flow needs it.

## Ordered Task List

This list maps the specification to the current code. All unchecked items are planned. Work on one small task at a time; explain the concept, implement, verify, review, and record evidence before marking it complete. The milestone 1 checklist below remains the summary of its exit criteria.

### Milestone 1: Incident API — complete

- [x] **API-01 — Create an incident in memory.** Connect `IncidentCreate` and `IncidentResponse` to `POST /incidents`. Generate the UUID and UTC creation timestamp on the server, save the incident in a process-local store, and return HTTP 201 with the response contract. Verify valid requests, unique IDs, timezone-aware timestamps, and HTTP 422 for invalid severity or client-supplied identity/time. Keep tests isolated from each other's stored data.
- [x] **API-02 — Retrieve an incident.** Add `GET /incidents/{id}` using the same store. Verify that create followed by get returns the same data, a well-formed but unknown UUID returns HTTP 404, and a malformed UUID returns HTTP 422. Depends on API-01.
- [x] **API-03 — Demonstrate and review milestone 1.** Add create/get examples to the README and explain that data is lost on restart and is not shared between processes. Run the backend tests and Ruff checks, record results, and manually exercise create/get through `/docs` or PowerShell. Review how routing, validation, identity generation, and storage fit together. Depends on API-01 and API-02.

  Documentation and verification completed on 2026-11-06: 33 tests passed, Ruff lint/format passed, and PowerShell requests against live Uvicorn confirmed create/get, failure responses, and data loss after restart. The README contains the request-flow explanation and review questions. The learner accepted completion and requested milestone 2 on 2026-11-06.

**Next working session:** INV-01 — investigation contracts and synthetic evidence. Review pagination, deterministic ordering, and repeatable seeding using the README questions. Investigation jobs and LLM calls remain planned.

### Milestone 2: persistent incident records

DB-01 uses SQLAlchemy models separate from the Pydantic HTTP contracts, per-request sessions, and Alembic-managed tables. Keep later steps small and preserve the existing API behavior.

- [x] **DB-01 — Add PostgreSQL persistence.** Introduce local database configuration, SQLAlchemy models, and an initial Alembic migration. Move create/get storage to PostgreSQL while preserving the HTTP contract. Verify migrations against an empty database and prove an incident survives an API restart. Document setup without committing credentials.
- [x] **DB-02 — List incidents and add synthetic seed data.** Provide a bounded, paginated incident list with deterministic ordering and a repeatable synthetic seed command. Verify empty lists, pagination, and create/get/list consistency against the database. Depends on DB-01.

### Milestone 3: one incident produces an investigation report

- [ ] **INV-01 — Define investigation contracts and a demo case.** Define investigation status, evidence, hypotheses, recommendations, and report contracts with durable incident/report relationships. Create the checkout-latency scenario with synthetic logs, metrics, deployment history, and expected evidence. Acceptance: fixtures load repeatably and tests validate the contracts. Depends on DB-01.
- [ ] **INV-02 — Collect evidence through mock adapters.** Introduce separate log, metric, and deployment adapters that return identifiable evidence. Acceptance: the demo case collects the expected evidence, and missing or unavailable sources are reported explicitly. Depends on INV-01.
- [ ] **INV-03 — Generate a structured report.** Build the initial triage → evidence → hypothesis → recommendation flow behind a provider interface. Add LangGraph when wiring the workflow and document its role. Acceptance: the report distinguishes observations from hypotheses, references valid evidence IDs, states uncertainty, and records provider failures. Use mocks in routine tests; record live provider verification separately. Depends on INV-02.
- [ ] **INV-04 — Expose and verify the incident-to-report flow.** Add investigation start/status/report endpoints and persist results. Acceptance: an integration test submits the synthetic incident, runs an investigation with mocked external services, and retrieves an evidence-linked report; failure states are retrievable too. Depends on INV-03.

### Milestone 4: retrieval with measurable quality

- [ ] **RAG-01 — Ingest and retrieve runbooks.** Choose pgvector or Chroma and record the tradeoff. Add repeatable ingestion, stable source references, and service/environment metadata filtering. Establish keyword and vector retrieval baselines before combining them; add reranking only if measurements justify it. Acceptance: the demo retrieves its relevant runbook and respects filters.
- [ ] **RAG-02 — Ground reports in retrieved material.** Connect retrieval to the investigation and validate citations. Acceptance: recommendations point to evidence or runbook passages, insufficient evidence produces an explicit limitation, and retrieved instructions cannot authorize tool execution. Depends on RAG-01 and INV-04.
- [ ] **EVAL-01 — Establish the evaluation baseline.** Create reviewed synthetic cases with expected evidence and plausible causes. Add DeepEval and deterministic checks for retrieval relevance, groundedness, correctness, citation validity, and unsafe recommendations. Acceptance: a reproducible run records dataset/configuration versions, results, latency, and cost where available; no improvement claims precede a measured comparison. Depends on RAG-02.

The first backend MVP is complete when a submitted incident yields a persisted report with valid evidence/runbook references and a recorded evaluation baseline. Remediation is a later, separately gated capability.

### Milestone 5: reliability, approved actions, and delivery

Split this milestone into smaller implementation tasks after the backend MVP works. Keep these outcomes in the indicated dependency order.

- [ ] **REL-01 — Run durable background investigations.** Add RabbitMQ workers, persistent job state, and reliable coordination between database writes and job publication. Implement bounded retries, backoff, dead-letter handling, and idempotency. Acceptance: duplicate delivery, worker crashes/restarts, and failures between saving and publishing have tested recovery behavior.
- [ ] **REL-02 — Bound failures and expose progress.** Add provider timeouts, bounded concurrency, rate limits, and SSE backed by durable status endpoints. Acceptance: provider timeouts reach a visible terminal or retry state, concurrency limits hold, and reconnecting clients recover progress without restarting work. Depends on REL-01.
- [ ] **SEC-01 — Enforce access and protect evidence.** Add authentication and role/service authorization, with tenant isolation if multi-tenancy is introduced. Redact secrets from logs/traces and test untrusted evidence handling. Acceptance: unauthorized reads/actions are denied and representative secret/prompt-injection cases are covered. Complete before exposing protected data or enabling remediation.
- [ ] **SAFE-01 — Add human-approved sandbox remediation.** Model proposed actions, scoped/expiring approvals, and audit events. Execute only allowlisted sandbox actions after authorized approval; record outcome verification and rollback instructions. Acceptance: denied, expired, out-of-scope, and reused approvals cannot trigger an action, and every attempted execution is audited. Depends on SEC-01 and durable workflow state.
- [ ] **OBS-01 — Make investigations observable.** Add structured logs and Langfuse/OpenTelemetry traces with evidence references, latency, token/cost metrics, queue depth, retries, and failures. Acceptance: one synthetic investigation can be traced across API and worker without exposing secrets or raw private chain-of-thought. Depends on REL-01 and the redaction controls in SEC-01.
- [ ] **UI-01 — Add the minimal dashboard.** After the backend incident-to-report flow works, support incident submission, status, evidence/report review, and action history. Add approval controls only after SAFE-01. Acceptance: the demo journey works with loading, empty, failure, and reconnect states, and authorization remains enforced by the backend.
- [ ] **SHIP-01 — Package, automate, and deploy.** Add reproducible Docker Compose setup and CI checks, then AWS infrastructure/configuration with least-privilege access and secrets handling. Acceptance: documented local startup and CI succeed; deployed health and investigation behavior are verified, with backup/recovery, troubleshooting, cleanup, and cost notes. Depends on the reliable backend flow; Kubernetes remains optional later work.
- [ ] **DEMO-01 — Publish measured portfolio evidence.** Run benchmark, failure-injection, and security scenarios; document architecture decisions and known limits; record the incident → report → approval → verification demo. Acceptance: public claims match recorded test/evaluation/deployment evidence and use only synthetic data. Depends on the capabilities demonstrated above.

### Known follow-up

- [ ] **DEV-01 — Revisit the TestClient deprecation warning when updating dependencies.** Investigate compatible test-client dependencies and verify the HTTP tests before recording the warning as resolved. Reconfirmed during API-01 verification on 2026-11-06.

## Milestone 1 Checklist

First outcome: **I can submit an incident and retrieve it.**

- [x] Set up `backend/`, a dependency manifest, and a local environment.
- [x] Document setup and run commands in a README.
- [x] Implement `GET /health` and verify its response locally.
- [x] Define incident request/response schemas and supported severity values.
- [x] Implement `POST /incidents`, returning an incident ID.
- [x] Implement `GET /incidents/{id}` with an appropriate missing-incident response.
- [x] Use an in-memory store initially; document that restart loses its data.
- [x] Test valid input, invalid severity, and an unknown incident ID.
- [x] Request-flow walkthrough and review questions provided; learner accepted milestone completion on 2026-11-06.

Example synthetic request:

```json
{
  "service": "checkout-api",
  "severity": "high",
  "summary": "Latency increased after the latest deployment"
}
```

Complete this milestone when create/get behavior and failure cases are verified and the learner can explain the implementation. PostgreSQL follows in milestone 2.

## Session Log

### 2026-10-14 — Learning plan established

- Completed: repository guide and shared learning tracker created; Claude entry point added.
- Agreed approach: one concept, one small implementation task, verification, then review.
- Validation: documentation read back and local references checked; no application code or tests exist yet.
- Next task: minimal backend setup and `GET /health`.

For future sessions, append the date, task, changes, checks/results, lessons, open questions or blockers, and the next small task. Update the current position and checklists to match.

### 2026-10-14 — Milestone 1 backend scaffold

- Completed: Git initialized on `main`; `.gitignore` added for environments, caches, local secrets/data, and future frontend/Terraform artifacts.
- Implemented: `backend/app/main.py` with `GET /health`, its HTTP contract test, Python/uv configuration, and README setup commands.
- Setup: isolated `backend/.venv` installed successfully using the locked dependencies and a workspace cache. Selected compatible cached versions because downloads were unavailable in this session; `uv.lock` records the exact versions.
- Verification: pytest — 1 passed; Ruff lint and formatting checks passed; `uv lock --check --offline` passed; live Uvicorn returned HTTP 200 for `/health` with `{"status":"ok"}` and for `/docs`. The temporary verification server was stopped.
- Observation: Starlette emits a deprecation warning for its HTTPX-based TestClient. Tests pass; revisit the supported test client dependency when updating dependencies.
- Learning notes: `.gitignore` excludes generated/private files; `pyproject.toml` declares dependencies and settings; `uv.lock` records resolved versions; `app.main:app` identifies the module and ASGI application object.
- Review pending: learner runs the app, traces the health request, and explains what the test verifies.
- Next task: define incident request/response schemas and supported severity values. Incident endpoints and storage remain planned.

### 2026-10-14 — Incident request and response schemas

- Learner feedback: scaffolding and run guidance are clear; proceed to the next task.
- Implemented: `IncidentSeverity`, `IncidentCreate`, and `IncidentResponse` in `backend/app/schemas.py`. Added Pydantic as a direct runtime dependency without changing locked package versions.
- Contract: required service (1–100 trimmed characters), summary (1–1,000 trimmed characters), and exact lowercase severity (`low`, `medium`, `high`, `critical`). Reject unexpected request fields. Response adds a UUID and a timezone-aware creation timestamp.
- Verification: 22 tests passed, including the existing health check; Ruff lint/format checks and offline lockfile validation passed. The existing TestClient deprecation warning remains.
- Learning notes: schemas describe accepted/returned data; Pydantic validates at model construction; response inheritance shares field validation. Schemas do not store incidents or generate identity/time.
- Review task: read the schemas, try the README model example, then change `high` to `urgent` to inspect the validation error.
- Next task: add `POST /incidents`, generating a UUID and UTC creation timestamp and saving the incident in memory. `GET /incidents/{id}` follows. HTTP incident endpoints and persistence remain planned.

### 2026-11-06 — Application review and ordered task list

- Reviewed: `Project.md`, shared instructions, README, learning tracker, backend app/schemas, dependency configuration, and existing test source.
- Findings: the application currently implements only `GET /health` and the incident data contracts. Create/get endpoints, persistence, workers, retrieval, reports, remediation, and the dashboard remain planned.
- Completed: added the ordered task list above with detailed acceptance criteria for the next three API tasks and outcome-level tasks for later milestones. Preserved the existing milestone sequence and learning workflow.
- Verification: checked the task list against the specification and current source. No application code or dependencies changed; automated tests were not rerun. The previous recorded result remains 22 passing tests with a TestClient warning.
- Next task: API-01 — explain and implement incident creation with server-generated identity/time and in-memory storage, then run focused HTTP tests and review the result.

### 2026-11-06 — API-01 incident creation

- Implemented: `POST /incidents` returns HTTP 201 with validated incident fields, a server-generated UUID v4, and a UTC creation timestamp. It saves the response model in an app-owned in-memory dictionary.
- Isolation: `create_app()` creates a separate dictionary for each app instance. Existing `app.main:app` startup still works; incident tests use fresh instances to avoid shared test data.
- Tests: eight new HTTP cases cover creation and storage, UUID/time correctness, trimmed text, distinct IDs for repeated submissions, invalid severity, blank service, client-supplied identity/time, and missing summary. Invalid requests return HTTP 422 without modifying storage.
- Verification: `uv run --no-sync --cache-dir .cache/uv python -m pytest` — **30 passed** on Python 3.12.12. Ruff lint and formatting checks passed after formatting the new test file; `git diff --check` passed. Dependencies and lockfile are unchanged. HTTP tests ran in process; no live Uvicorn smoke test was run for this task.
- Warnings: the existing Starlette/HTTPX TestClient deprecation remains. Pytest also reported that its existing `.pytest_cache` could not save cache data because of a local permission error; tests completed successfully. Cache permissions were not changed.
- Documentation: added a PowerShell POST example and the create-request walkthrough to the README; documented data loss on restart/reload and lack of cross-process sharing. Marked API-01 complete.
- Learning notes: request schemas validate client input; the handler owns generated identity/time and storage. `response_model` defines the returned contract. A fresh app factory makes test state independent; an in-memory dictionary is not durable persistence.
- Review pending: learner traces the POST handler and explains why invalid input never reaches storage, why the client cannot choose `id`/`created_at`, and why incidents disappear after a restart.
- Next task: API-02 — add `GET /incidents/{id}` with successful retrieval, HTTP 404 for an unknown UUID, and HTTP 422 for a malformed UUID.

### 2026-11-06 — API-02 incident retrieval

- Implemented: `GET /incidents/{incident_id}` uses the existing app-owned store and returns the original incident with HTTP 200. Unknown UUIDs return HTTP 404 with `{"detail":"Incident not found"}`; malformed UUIDs return HTTP 422 through path validation.
- Tests: three new HTTP tests verify correct retrieval across multiple incidents, an unknown UUID without changing an existing record, and a malformed path value.
- Verification: backend pytest — **33 passed** on Python 3.12.12; Ruff lint and formatting passed. No dependencies changed. HTTP verification ran in process; a live server demonstration remains part of API-03.
- Warnings: the existing TestClient deprecation and pytest cache permission warnings remain; neither failed the test run.
- Documentation: README now captures the POST response and uses its ID for GET, with documented 200/404/422 outcomes. Displayed inline diffs for each logical change as requested.
- Learning notes: `incident_id: UUID` validates and converts the path value before the handler runs. A valid identifier can still refer to a missing record; that is a lookup failure (404), distinct from invalid input (422).
- Review pending: learner explains the create/get flow, the 404/422 distinction, and process-local storage limitations. Milestone 1 remains in progress until demonstration and review.
- Next task: API-03 — run the documented create/get example against a local server and review milestone 1 before PostgreSQL.

### 2026-11-06 — API-03 demonstration and review guide

- Completed: extended the README create/get examples with readable JSON, comparison of all five response fields, a sample response, restart demonstration instructions, and `/docs` failure-case exercises. Added the complete routing → validation → identity/storage → retrieval → response walkthrough and learner review questions.
- Scope: existing API handlers, schemas, tests, dependencies, and lockfile were preserved. API-03 needed documentation and demonstration rather than another endpoint.
- Automated verification: `uv run --no-sync --cache-dir .cache/uv python -m pytest` — **33 passed** on Python 3.12.12. `uv run --no-sync --cache-dir .cache/uv ruff check .` and `uv run --no-sync --cache-dir .cache/uv ruff format --check .` passed (6 Python files already formatted). The existing TestClient deprecation and pytest cache permission warnings remain.
- Live verification: started Uvicorn from the uv-managed environment on `127.0.0.1:7047` because port 8000 was occupied. PowerShell confirmed `/health` and `/docs` returned 200, POST returned 201, and GET returned 200 with all five fields matching. Created incident: `a0300dc3-45eb-4ab2-ad41-336c4dbd2ecd`, UTC timestamp `2026-11-06T13:35:40.289022Z`.
- Failure and lifecycle evidence: an unknown UUID returned 404, a malformed UUID returned 422, and POST with severity `urgent` returned 422. Stopped and restarted the temporary server on the same port; GET for the previously created incident returned 404, confirming restart data loss. The temporary server was stopped after verification. The pre-existing server on port 8000 was left running.
- Learning notes: routing chooses the handler; Pydantic validates body/path input before it runs; POST generates identity/time and writes to the app-owned dictionary; GET reads the original record. A valid UUID can identify a missing record (404), while a malformed value is invalid input (422). Separate app processes own separate dictionaries; PostgreSQL will provide durable shared storage.
- Review status: implementation, documentation, and demonstration are complete. Learner understanding has not yet been assessed, so API-03 and milestone 1 remain open for review. Use the four README questions to explain validation, 404 versus 422, server-generated fields, and process-local data loss.
- Next task: complete the learner review, then DB-01 — add PostgreSQL persistence while preserving create/get behavior.

### 2026-11-06 — Milestone 1 accepted; DB-01 PostgreSQL persistence

- Learner decision: explicitly requested API-03 be marked complete and to move to the next stage. Marked API-03 and milestone 1 complete without claiming an additional learner assessment took place.
- Implemented: PostgreSQL environment configuration, SQLAlchemy `Incident` model and constraints, a repository, and request-scoped sessions. POST generates identity/time and commits before returning 201; GET uses the same durable table. Preserved request/response fields and 200/201/404/422 behavior. Synchronous handlers run database work in FastAPI's thread pool; lifespan shutdown disposes the engine.
- Migration: Alembic revision `0001` creates the incident table. Applied successfully to the newly initialized local database. Repeated upgrade is safe; model/migration drift check passed. Tests also exercised downgrade/upgrade only inside generated temporary schemas. No existing incident table was dropped; milestone 1's transient in-memory records were not imported.
- Local setup: started installed Docker Desktop and the `postgres:17` Compose service on `127.0.0.1:5433`, backed by the `inspector_postgres_data` volume. Created an ignored `.env` with a generated local password; `.env.example` contains only placeholders. README documents configuration, migration/start commands, persistence demonstration, test isolation, and data-loss implications of downgrade or volume removal.
- Test design: default HTTP tests use a repository double without database access. `--postgres` additionally runs the HTTP contracts through real database sessions and tests migration/model agreement, shared records across independent app instances, restart survival, database constraints, and recovery after a failed commit. Each database test owns a unique `inspector_test_*` schema and removes only that schema.
- Verification: **54 passed** with `uv run --no-sync --cache-dir .cache/uv --env-file ../.env python -m pytest --postgres` on Python 3.12.12. Ruff lint and formatting passed (14 Python files). `alembic check` reported no new upgrade operations; offline lockfile validation passed. The pre-existing TestClient deprecation and pytest cache permission warnings remain. An initial formatting failure was corrected; the new Alembic configuration warning was resolved with `path_separator = os`.
- Final checks: default offline run — **38 passed, 16 PostgreSQL cases skipped** without `--postgres`; final Ruff lint/format and `git diff --check` passed. `alembic current` reported `0001 (head)`. Confirmed `.env` is ignored and untracked; Compose reports PostgreSQL healthy.
- Live evidence: separate Uvicorn processes on ports 6879 and 6880 read incident `9b7bac10-6a8c-49de-8835-55c33aae8d5a`, created at `2026-11-06T13:54:59.591146Z`. POST returned 201; GET returned 200 with identical data in the second simultaneous process and again after restarting the first process. Both temporary API processes were stopped; PostgreSQL remains running for local use. Demo evidence is in ignored `backend/.cache/db01-demo.json`.
- Learning notes: Pydantic schemas validate HTTP data, SQLAlchemy models map rows, and Alembic migrations change the stored schema. A successful commit makes the incident durable outside the API process. Session cleanup releases connections and rolls back unfinished work. A named volume retains PostgreSQL files when a container is stopped or recreated; explicit volume deletion or schema downgrade can remove data.
- Next task: DB-02 — add bounded incident pagination with deterministic ordering and a repeatable synthetic seed command; verify empty lists and create/get/list consistency. The README contains the persistence review questions.

### 2026-11-06 — Automatic dotenv loading

- Requested: load `.env` automatically instead of repeating `uv run --env-file ../.env`.
- Implemented: added `python-dotenv` as a direct runtime dependency and updated `uv.lock`. Shared `get_database_url()` loads the explicit repository-root `.env` when configuration is requested, covering both API startup and Alembic without import-time loading. Existing environment variables retain priority (`override=False`); UTF-8 files with or without a Windows BOM are accepted. Missing file handling and required-password validation are preserved.
- Tests: isolated configuration tests from the developer's real `.env` and added cases for file-supplied settings, environment precedence, and working-directory independence. Loaded synthetic environment values are restored after each test.
- Documentation: removed required `--env-file` flags from current README commands and updated `.env.example`; documented environment precedence and restarting the API after configuration changes. Historical commands in earlier session logs remain as executed.
- Verification: **57 passed** with `uv run --no-sync --cache-dir .cache/uv python -m pytest --postgres`, without `--env-file`. Ruff lint/format and offline lockfile checks passed; `alembic current` loaded configuration automatically and reported `0001 (head)`. Existing TestClient and pytest cache permission warnings remain.
- Live verification: ran the existing Uvicorn HTTP demo without `--env-file`. POST returned 201 and GET returned identical data across a second process and after restarting the first. Synthetic incident ID: `e6f45121-7daf-4751-a754-16e8fc9468d4`. Both temporary servers were stopped; ignored demo evidence was refreshed.
- Learning notes: python-dotenv fills missing process environment values from the chosen file; SQLAlchemy configuration still reads normal environment variables. A fixed file path prevents terminal location from selecting a different `.env`. DB-02 remains next; no incident contract or database schema changed.

### 2026-11-06 — DB-02 paginated listing and repeatable seed data

- Implemented: `GET /incidents` returns HTTP 200 with `IncidentPage` (`items`, `limit`, `offset`, `has_more`). Default limit is 20, accepted range is 1–100, and offset is a nonnegative signed 64-bit integer. Invalid values return 422. Existing create/get contracts are unchanged.
- Storage/query behavior: repository listing orders by creation time descending, then UUID descending for equal timestamps. Fetches at most `limit + 1` rows to determine `has_more`, returns at most `limit`, and does not issue a total-count query. Empty and past-end pages return an empty list. Offset pagination is deterministic for unchanged data; inserts between requests can shift page boundaries and deep offsets require more skipping.
- Seed command: `uv run python -m app.seed` inserts three synthetic checkout/payment/inventory incidents, using fixed UTC timestamps and deterministic UUID v5 IDs. The command uses the same automatic dotenv configuration, one database transaction, and PostgreSQL `ON CONFLICT (id) DO NOTHING`. It adds missing IDs while preserving edited seed rows and unrelated records; it does not reset data or create tables.
- Tests: added offline/real-PostgreSQL list contracts for empty lists, page boundaries, repeated pages, invalid query values, and create/get/list consistency. PostgreSQL-specific tests prove time/UUID ordering across page boundaries, seed command repeatability and read consistency, preservation of existing records, and rollback without partial seed rows.
- Verification: **87 passed** using `uv run --no-sync --cache-dir .cache/uv python -m pytest --postgres` on Python 3.12.12. Ruff lint/format passed (17 Python files); `alembic check` reported no new upgrade operations. Dependencies, lockfile, and database schema did not change. Existing TestClient deprecation and pytest cache permission warnings remain.
- Live evidence: executed the seed CLI twice in separate processes against local PostgreSQL. First run inserted 3/skipped 0; second inserted 0/skipped 3. Temporary Uvicorn on port 4861 returned 7 incidents across 4 pages of size 2, with deterministic ordering, no duplicate IDs, all seed IDs present, and each list item identical to GET. A new synthetic POST (`ca15380c-cad6-4cc3-a758-5c9ad6006565`) matched GET/list; invalid limit returned 422 and a past-end offset returned an empty page. The temporary server was stopped; PostgreSQL remains running. Ignored evidence: `backend/.cache/db02-demo.json`.
- Documentation: README now describes pagination parameters/envelope, PowerShell paging, seed usage and repeatability, transaction ownership, and offset limitations. Added learning questions for UUID tie-breaking, the extra fetched row, and conflict handling. Milestone 2 is complete; learner review questions remain available without claiming a separate assessment took place.
- Next task: INV-01 — define incident-linked investigation status, evidence, hypotheses, recommendations, and report contracts, then add the checkout-latency evidence fixtures. No worker, investigation execution, or LLM calls were added in DB-02.
