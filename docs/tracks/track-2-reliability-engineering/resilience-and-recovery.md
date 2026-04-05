# Track 2 Resilience and Recovery

## Reliability mechanisms

### 1. Database connection resilience

Configured in `app/database.py`:

- `pool_size=20`
- `max_overflow=10`
- `pool_timeout=30`
- `pool_pre_ping=True`

Impact:

- stale connections are detected before use
- controlled behavior under connection pressure

### 2. Process recovery inside container

`docker-entrypoint.sh` runs uvicorn in an infinite restart loop:

1. start uvicorn
2. if process exits, log status
3. sleep 1 second
4. restart uvicorn

Impact:

- process crashes do not permanently take down containerized app runtime

### 3. Service health checks

- `/health` endpoint returns `{"status": "ok"}`
- compose DB healthcheck uses `pg_isready`

Impact:

- startup dependency ordering and liveness verification become deterministic

### 4. Safe async event logging

URL workflows emit events through FastAPI background tasks.

Impact:

- request responses are not blocked by non-critical event persistence
- event logging failures do not block the primary URL operation

## Recovery runbook (quick)

1. Check service state:

```bash
docker compose ps
```

2. Inspect application logs:

```bash
docker compose logs --tail=200 app
```

3. Verify app responsiveness:

```bash
curl http://localhost:8000/health
```

4. Inspect diagnostics:

```bash
curl http://localhost:8000/metrics/json
curl "http://localhost:8000/logs?limit=50"
```

## Known limitations

- No explicit readiness endpoint with DB ping yet.
- No distributed tracing IDs in request logs.
- No retry queue/dead-letter behavior for background task failures.

These are acceptable for current scope but should be included in future hardening work.
