import json
import logging
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Header, HTTPException, Request, Response, status
from pydantic import BaseModel, Field
from qdrant_client import AsyncQdrantClient

from .auth import AuthenticationError, verify
from .config import get_settings
from .db import get_run, initialize as initialize_db, make_engine, ready as db_ready, save_run
from .junit import JUnitError, parse_failures
from .qdrant_store import index_and_search, initialize as initialize_qdrant, ready as qdrant_ready

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("ci_failure_spike")


class RunMetadata(BaseModel):
    repository: str = Field(min_length=1, max_length=300)
    run_id: str = Field(min_length=1, max_length=100)
    run_attempt: int = Field(ge=1, le=1000)
    commit_sha: str = Field(min_length=7, max_length=100)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    app.state.engine = make_engine(settings.database_url)
    app.state.qdrant = AsyncQdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key)
    await initialize_db(app.state.engine)
    await initialize_qdrant(app.state.qdrant)
    yield
    await app.state.qdrant.close()
    await app.state.engine.dispose()


app = FastAPI(title="CI Failure Deployment Spike", version="0.1.0", lifespan=lifespan)


@app.middleware("http")
async def request_context(request: Request, call_next):
    started = time.perf_counter()
    request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
    try:
        response = await call_next(request)
    except Exception:
        logger.exception(json.dumps({"event": "request_failed", "request_id": request_id, "path": request.url.path}))
        raise
    response.headers["x-request-id"] = request_id
    logger.info(
        json.dumps(
            {
                "event": "request_complete",
                "request_id": request_id,
                "path": request.url.path,
                "status": response.status_code,
                "duration_ms": round((time.perf_counter() - started) * 1000, 2),
            }
        )
    )
    return response


@app.get("/health/live")
async def live():
    return {"status": "alive"}


@app.get("/health/ready")
async def ready(request: Request, response: Response):
    dependencies: dict[str, str] = {}
    for name, check in (
        ("postgres", lambda: db_ready(request.app.state.engine)),
        ("qdrant", lambda: qdrant_ready(request.app.state.qdrant)),
    ):
        try:
            await check()
            dependencies[name] = "ok"
        except Exception:
            dependencies[name] = "unavailable"
    is_ready = "unavailable" not in dependencies.values()
    if not is_ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return {"status": "ready" if is_ready else "not_ready", "dependencies": dependencies}


@app.post("/api/v1/ci-runs")
async def ingest(
    request: Request,
    x_ci_timestamp: str | None = Header(default=None),
    x_ci_signature: str | None = Header(default=None),
    x_ci_metadata: str | None = Header(default=None),
):
    settings = get_settings()
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > settings.max_body_bytes:
        raise HTTPException(status_code=413, detail="request body too large")
    body = await request.body()
    if len(body) > settings.max_body_bytes:
        raise HTTPException(status_code=413, detail="request body too large")
    try:
        verify(
            settings.ingest_hmac_secret,
            x_ci_timestamp,
            x_ci_signature,
            body,
            settings.signature_tolerance_seconds,
        )
    except AuthenticationError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    try:
        metadata = RunMetadata.model_validate_json(x_ci_metadata or "")
        failures = parse_failures(body, settings.max_failures)
    except (ValueError, JUnitError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    run, rows, created = await save_run(request.app.state.engine, metadata.model_dump(), failures)
    matches = await index_and_search(request.app.state.qdrant, run.id, rows)
    return {"id": run.id, "created": created, "failure_count": len(rows), "similar": matches}


@app.get("/api/v1/ci-runs/{run_pk}")
async def read_run(run_pk: int, request: Request):
    run, failures = await get_run(request.app.state.engine, run_pk)
    if not run:
        raise HTTPException(status_code=404, detail="run not found")
    return {
        "id": run.id,
        "repository": run.repository,
        "run_id": run.run_id,
        "run_attempt": run.run_attempt,
        "commit_sha": run.commit_sha,
        "failures": [{"node_id": item.node_id, "message": item.message} for item in failures],
    }

