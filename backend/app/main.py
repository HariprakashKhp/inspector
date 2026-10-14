"""FastAPI entry point for the Inspector backend."""

from fastapi import FastAPI

app = FastAPI(
    title="Inspector API",
    description="AI incident investigation learning project",
    version="0.1.0",
)


@app.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    """Confirm the API is responding; dependency readiness comes later."""
    return {"status": "ok"}
