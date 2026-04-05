import csv
import json
import logging
import os
import time
from pathlib import Path

import psutil
import uvicorn
from fastapi import Request
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app import create_app
from app.database import Base, SessionLocal, engine
from app.models.domain import Event, URL, User
from app.observability import get_system_metrics, setup_logging

app = create_app()
log_file_path = setup_logging()
logger = logging.getLogger("app")

try:
    from prometheus_fastapi_instrumentator import Instrumentator
    from prometheus_client import Gauge
    
    cpu_usage_gauge = Gauge(
        "process_cpu_usage_percent",
        "Current CPU usage percentage of the host",
    )
    
    Instrumentator(
        should_group_status_codes=False,
        excluded_handlers=["/metrics", "/health"],
    ).instrument(app).expose(app, include_in_schema=True, tags=["observability"])

except ImportError:
    logger.warning("Prometheus metrics dependencies not found. Skipping instrumentation.")


@app.middleware("http")
async def request_metrics_middleware(request: Request, call_next):
    if "cpu_usage_gauge" in globals():
        cpu_usage_gauge.set(psutil.cpu_percent(interval=None))
    return await call_next(request)

@app.get("/metrics/json", tags=["observability"])
def metrics_json():
    return get_system_metrics()

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

        # Seed Users
        users_file = seed_dir / "users.csv"
        if users_file.exists():
            with users_file.open("r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    db.add(User(id=int(row["id"]), username=row["username"], email=row["email"]))
            db.commit()

        # Seed URLs
        urls_file = seed_dir / "urls.csv"
        if urls_file.exists():
            with urls_file.open("r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    db.add(URL(
                        id=int(row["id"]),
                        user_id=int(row["user_id"]),
                        short_code=row["short_code"],
                        original_url=row["original_url"],
                        title=row.get("title", ""),
                        is_active=row.get("is_active", "true").lower() == "true"
                    ))
            db.commit()

        # Seed Events
        events_file = seed_dir / "events.csv"
        if events_file.exists():
            with events_file.open("r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    details = json.loads(row["details"].replace("'", '"')) if row.get("details") else {}
                    db.add(Event(
                        id=int(row["id"]),
                        url_id=int(row["url_id"]),
                        user_id=int(row["user_id"]),
                        event_type=row["event_type"],
                        details=details
                    ))
            db.commit()

        # Sync sequences for PostgreSQL
        db.execute(text("SELECT setval('users_id_seq', (SELECT MAX(id) FROM users))"))
        db.execute(text("SELECT setval('urls_id_seq', (SELECT MAX(id) FROM urls))"))
        db.execute(text("SELECT setval('events_id_seq', (SELECT MAX(id) FROM events))"))
        db.commit()
        logger.info("Database seeded successfully", extra={"component": "seed"})

    except (SQLAlchemyError, Exception) as exc:
        db.rollback()
        logger.exception("Database seeding failed", extra={"component": "seed", "error": str(exc)})
    finally:
        db.close()

@app.on_event("startup")
def startup() -> None:
    try:
        Base.metadata.create_all(bind=engine)
        if os.getenv("ENABLE_STARTUP_SEED", "false").lower() in {"1", "true", "yes", "on"}:
            seed_database()
    except Exception as exc:
        logger.exception(
            "Startup database initialization failed",
            extra={"component": "startup", "error": str(exc)},
        )

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8000")),
        access_log=False,
    )
