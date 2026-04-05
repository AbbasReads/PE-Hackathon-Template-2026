# Track 2 Error Handling Contract

## Design principles

- Clients should always receive machine-readable JSON errors.
- Unexpected internal errors should not expose stack traces.
- Known failures should return endpoint-specific and human-readable details.

## Status code matrix

| Status | Category | Returned by |
|---|---|---|
| 400 | Request accepted but semantically invalid by business rule | Route logic (`users`, `bulk import`) |
| 404 | Resource/route not found | FastAPI router or explicit checks |
| 422 | Request shape/type validation failed | FastAPI + Pydantic |
| 500 | Unhandled internal exception | Global exception handler |

## Canonical error bodies

### 400 examples

```json
{"detail": "Only CSV files allowed"}
```

```json
{"detail": "CSV must include username and email columns"}
```

### 404 examples

```json
{"detail": "User not found"}
```

```json
{"detail": "URL not found"}
```

### 422 example shape

```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "value is not a valid email address",
      "type": "value_error"
    }
  ]
}
```

### 500 fallback

```json
{"detail": "Internal Server Error"}
```

## Route-level failure examples

- `POST /users`: duplicate username/email -> `400`
- `POST /users/bulk`: malformed CSV -> `400`
- `POST /urls`: missing owner -> `404`
- `GET /urls/{id}`: inactive URL -> `404`
- Any unhandled exception -> `500`

## Test coverage

Error behavior is validated in `tests/test_error_handling.py` including:

- strict-type violations
- malformed payloads
- duplicate resource guards
- unknown route behavior
- simulated runtime failure path
