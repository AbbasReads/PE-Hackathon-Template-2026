# Track 1 Developer Workflow

## Local development (Python)

1. Create or activate your Python environment.
2. Install dependencies:

```bash
python -m pip install -r requirements.txt
```

3. Configure environment:

```bash
cp .env.example .env
```

4. Run app:

```bash
python run.py
```

## Local development (Docker)

```bash
docker compose up -d --build
```

Then validate:

```bash
curl http://localhost:8000/health
```

## Running tests

```bash
python -m pytest -q
```

## Typical contributor checklist

When you add or modify an API endpoint:

1. Update schemas in `app/models/schemas.py` if request/response changes.
2. Add route logic with explicit error handling.
3. Add integration tests in `tests/test_integration.py`.
4. Add error-path tests in `tests/test_error_handling.py`.
5. Update track docs (`overview` and `api-reference`) for behavior changes.

## Debugging tips

- Check structured logs through:

```bash
curl "http://localhost:8000/logs?limit=50"
```

- Inspect runtime metrics through:

```bash
curl http://localhost:8000/metrics/json
```

## Common mistakes

- Sending string values where strict integer IDs are required.
- Forgetting that inactive URLs return `404` on fetch/redirect.
- Assuming event writes are synchronous (they are background tasks for URL flows).
