# Error Handling

## 422 responses

- Invalid request payloads are rejected with JSON validation errors from FastAPI.
- Example cases include invalid emails on `POST /users` and malformed request bodies on `POST /urls`.

## 404 responses

- Unknown routes use FastAPI's default JSON 404 response: `{"detail": "Not Found"}`.
- Known routes that cannot find a resource return route-specific JSON errors:
  - `GET /users/{id}` and `PUT /users/{id}` return `{"detail": "User not found"}`.
  - `GET /urls/{id}` and `PUT /urls/{id}` return `{"detail": "URL not found"}`.
  - `POST /urls` returns `{"detail": "User not found"}` when the owning user does not exist.
  - `POST /users/bulk` returns `{"detail": "Only CSV files allowed"}` when a non-CSV file is uploaded.

## 500 responses

- The app has a global exception handler in `app.create_app()` that converts unexpected server errors into JSON.
- Unhandled exceptions return `500 Internal Server Error` with the body `{"detail": "Internal Server Error"}`.
- This keeps the API response format predictable and avoids leaking stack traces to clients.
