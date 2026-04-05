import csv
import json
import logging
import time
from pathlib import Path

import uvicorn
from fastapi import Query, Request
from fastapi.responses import JSONResponse
import psutil
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app import create_app
from app.database import Base, SessionLocal, engine
from app.models.domain import Event, URL, User
from app.observability import get_system_metrics, read_recent_logs, setup_logging

try:
    from prometheus_fastapi_instrumentator import Instrumentator
    from prometheus_client import Gauge
except ImportError:  # pragma: no cover - optional local dependency
    Instrumentator = None
    Gauge = None


app = create_app()
log_file_path = setup_logging()
logger = logging.getLogger("app")

cpu_usage_gauge = (
    Gauge(
        "process_cpu_usage_percent",
        "Current CPU usage percentage of the host",
    )
    if Gauge is not None
    else None
)

if Instrumentator is not None:
    Instrumentator(
        should_group_status_codes=False,
        excluded_handlers=["/metrics", "/health"],
    ).instrument(app).expose(app, include_in_schema=True, tags=["observability"])


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    if cpu_usage_gauge is not None:
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


@app.get("/metrics/json", tags=["observability"])
def metrics_json():
    return get_system_metrics()


@app.get("/logs", tags=["observability"])
def logs(limit: int = Query(default=100, ge=1, le=1000)):
    return {"items": read_recent_logs(log_file_path, limit=limit)}


def seed_database() -> None:
    seed_dir = Path("seed_data")
    if not seed_dir.exists():
        logger.warning("Seed data directory not found", extra={"component": "seed"})
        return

    db = SessionLocal()
    try:
        if db.query(User).first():
            return

        logger.info("Seeding database", extra={"component": "seed"})

        with (seed_dir / "users.csv").open("r", encoding="utf-8") as file_obj:
            reader = csv.DictReader(file_obj)
            for row in reader:
                db.add(User(id=int(row["id"]), username=row["username"], email=row["email"]))
        db.commit()

        with (seed_dir / "urls.csv").open("r", encoding="utf-8") as file_obj:
            reader = csv.DictReader(file_obj)
            for row in reader:
                db.add(
                    URL(
                        id=int(row["id"]),
                        user_id=int(row["user_id"]),
                        short_code=row["short_code"],
                        original_url=row["original_url"],
                        title=row["title"],
                        is_active=row["is_active"].lower() == "true",
                    )
                )
        db.commit()

        with (seed_dir / "events.csv").open("r", encoding="utf-8") as file_obj:
            reader = csv.DictReader(file_obj)
            for row in reader:
                details = json.loads(row["details"].replace("'", '"')) if row["details"] else {}
                db.add(
                    Event(
                        id=int(row["id"]),
                        url_id=int(row["url_id"]),
                        user_id=int(row["user_id"]),
                        event_type=row["event_type"],
                        details=details,
                    )
                )
        db.commit()

        try:
            db.execute(text("SELECT setval('users_id_seq', (SELECT MAX(id) FROM users))"))
            db.execute(text("SELECT setval('urls_id_seq', (SELECT MAX(id) FROM urls))"))
            db.execute(text("SELECT setval('events_id_seq', (SELECT MAX(id) FROM events))"))
            db.commit()
        except SQLAlchemyError:
            db.rollback()

        logger.info("Database seeded successfully", extra={"component": "seed"})
    except Exception as exc:
        db.rollback()
        logger.exception(
            "Database seeding failed",
            extra={"component": "seed", "error": str(exc)},
        )
    finally:
        db.close()


@app.on_event("startup")
def startup() -> None:
    try:
        Base.metadata.create_all(bind=engine)
        seed_database()
    except Exception as exc:
        logger.exception(
            "Startup database initialization failed",
            extra={"component": "startup", "error": str(exc)},
        )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
