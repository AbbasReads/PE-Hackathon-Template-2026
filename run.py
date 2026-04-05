import uvicorn
from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
import logging
import time
import os

from fastapi import FastAPI, Query, Request
from fastapi.responses import JSONResponse
from app import create_app
from app.database import Base, engine, SessionLocal
from app.routes import users, urls, events
from app.models.domain import User, URL, Event
from app.observability import get_system_metrics, read_recent_logs, setup_logging
import csv
import json

# ---------------------------------------------------------------------------
# Prometheus instrumentation
# ---------------------------------------------------------------------------
from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_client import Gauge

# Custom gauge: CPU usage percentage (updated every request via middleware)
cpu_usage_gauge = Gauge(
    "process_cpu_usage_percent",
    "Current CPU usage percentage of the host",
)

import psutil

app = FastAPI(title="Hackathon URL Shortener", default_response_class=ORJSONResponse)
log_file_path = setup_logging()
logger = logging.getLogger("app")

Base.metadata.create_all(bind=engine)

app.include_router(users.router)
app.include_router(urls.router)
app.include_router(events.router)

# Expose Prometheus-format /metrics endpoint (auto-instruments requests)
Instrumentator(
    should_group_status_codes=False,
    excluded_handlers=["/metrics", "/health"],
).instrument(app).expose(app, include_in_schema=True, tags=["observability"])


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    # Update CPU gauge on every request so Prometheus gets fresh values
    cpu_usage_gauge.set(psutil.cpu_percent(interval=None))

    start = time.perf_counter()
    response = None
    try:
        response = await call_next(request)
        return response
    finally:
        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        logger.info(
            "HTTP request",
            extra={
                "component": "http",
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code if response else 500,
                "duration_ms": duration_ms,
                "client_ip": request.client.host if request.client else None,
            },
        )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception(
        "Unhandled exception",
        extra={
            "component": "http",
            "path": request.url.path,
            "method": request.method,
        },
    )
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


# JSON metrics endpoint (moved from /metrics to avoid conflict with Prometheus)
@app.get("/metrics/json", tags=["observability"])
def metrics_json():
    return get_system_metrics()


@app.get("/logs", tags=["observability"])
def logs(limit: int = Query(default=100, ge=1, le=1000)):
    return {"items": read_recent_logs(log_file_path, limit=limit)}


# ---------------------------------------------------------------------------
# Debug endpoints (for testing alerts — disable in production)
# ---------------------------------------------------------------------------
@app.get("/debug/error", tags=["debug"])
def debug_error():
    """Intentionally raise a 500 error for testing HighErrorRate alerts."""
    raise RuntimeError("Intentional error for alert testing")


@app.get("/debug/cpu-spike", tags=["debug"])
def debug_cpu_spike():
    """Burn CPU for ~30 seconds to test HighCPU alerts."""
    import time as _t
    end = _t.time() + 30
    while _t.time() < end:
        _ = sum(i * i for i in range(10_000))
    return {"status": "done", "message": "CPU spike completed"}


# ---------------------------------------------------------------------------
# Database seeding
# ---------------------------------------------------------------------------
def seed_database():
    db = SessionLocal()
    if not db.query(User).first():
        logger.info("Seeding database", extra={"component": "seed"})
        try:
            with open("seed_data/users.csv", "r") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    db.add(User(id=int(row['id']), username=row['username'], email=row['email']))
            db.commit()

            with open("seed_data/urls.csv", "r") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    is_active = row['is_active'].lower() == 'true'
                    db.add(URL(id=int(row['id']), user_id=int(row['user_id']), short_code=row['short_code'], original_url=row['original_url'], title=row['title'], is_active=is_active))
            db.commit()

            with open("seed_data/events.csv", "r") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    details = json.loads(row['details'].replace("'", '"')) if row['details'] else {}
                    db.add(Event(id=int(row['id']), url_id=int(row['url_id']), user_id=int(row['user_id']), event_type=row['event_type'], details=details))
            db.commit()

            # Reset auto-increment sequences for PostgreSQL
            from sqlalchemy import text
            db.execute(text("SELECT setval('users_id_seq', (SELECT MAX(id) FROM users))"))
            db.execute(text("SELECT setval('urls_id_seq', (SELECT MAX(id) FROM urls))"))
            db.execute(text("SELECT setval('events_id_seq', (SELECT MAX(id) FROM events))"))
            db.commit()

            logger.info(
                "Database seeded successfully",
                extra={"component": "seed"},
            )
        except Exception as e:
            logger.exception(
                "Database seeding failed",
                extra={"component": "seed", "error": str(e)},
            )
            db.rollback()
    db.close()

seed_database()

if __name__ == "__main__":
    uvicorn.run("run:app", host="0.0.0.0", port=8000, workers=4)
