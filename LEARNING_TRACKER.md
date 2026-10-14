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

- Current milestone: 1 — Incident API.
- Status: in progress; scaffolding, health endpoint, and incident schemas verified.
- Existing artifacts: shared guidance, README, Git repository, `.gitignore`, and the backend app, incident schemas, tests, dependency manifest, lockfile, and local environment.
- Next task: implement `POST /incidents` with server-generated identity/time and an in-memory store.
- Setup decisions: Python 3.12.12, uv, and `backend/app/` with component-local tests. Learner reported the scaffold and run guidance clear; incident schema review is next.

## Milestone Roadmap

| Milestone | Working outcome | Main learning | Status |
|---|---|---|---|
| 1. Incident API | Submit and retrieve a synthetic incident | FastAPI, schemas, validation, HTTP, tests | In progress |
| 2. Persistence | Incidents survive an application restart | PostgreSQL, migrations, transactions | Planned |
| 3. Investigation | Synthetic evidence produces a structured report | Evidence adapters, LLM output, uncertainty | Planned |
| 4. Retrieval and evaluation | Reports cite relevant runbooks; quality is measured | RAG, labeled datasets, evaluation | Planned |
| 5. Reliability and delivery | Jobs recover from failures; approved sandbox actions are audited | Queues, retries, idempotency, security, observability, deployment | Planned |

Break later milestones into smaller tasks when reached. Add the dashboard after the incident-to-report backend works; expand infrastructure when the working flow needs it.

## Milestone 1 Checklist

First outcome: **I can submit an incident and retrieve it.**

- [x] Set up `backend/`, a dependency manifest, and a local environment.
- [x] Document setup and run commands in a README.
- [x] Implement `GET /health` and verify its response locally.
- [x] Define incident request/response schemas and supported severity values.
- [ ] Implement `POST /incidents`, returning an incident ID.
- [ ] Implement `GET /incidents/{id}` with an appropriate missing-incident response.
- [ ] Use an in-memory store initially; document that restart loses its data.
- [ ] Test valid input, invalid severity, and an unknown incident ID.
- [ ] Explain the request flow, validation, ID generation, and storage limitations.

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
