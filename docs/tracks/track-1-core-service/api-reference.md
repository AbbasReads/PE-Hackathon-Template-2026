# Track 1 API Reference

This reference focuses on behavior a consumer of the API needs to understand quickly.

## Base URL

- Local app container behind NGINX: `http://localhost:8000`
- Direct app (single service profile): `http://localhost:8000`

## Authentication

No authentication is implemented in the current project scope.

## Content types

- JSON APIs: `application/json`
- Bulk user upload: `multipart/form-data` with CSV file

## Users API

### Create user

`POST /users`

Request body:

```json
{
  "username": "alice",
  "email": "alice@example.com"
}
```

Success: `201 Created`

```json
{
  "id": 1,
  "username": "alice",
  "email": "alice@example.com",
  "created_at": "2026-04-05T10:00:00"
}
```

Common errors:

- `400`: duplicate email
- `400`: duplicate username
- `422`: validation failure

### Bulk import users

`POST /users/bulk`

Form field:

- `file`: CSV file

Expected CSV columns:

- `username`
- `email`

Behavior:

- Invalid rows are skipped.
- Case-insensitive email dedupe is enforced.
- If CSV contains `id` column, duplicate usernames are permitted (seed-compatible behavior).

Success response:

```json
{"count": 12}
```

Error responses:

- `400`: non-CSV file
- `400`: non-UTF8 CSV
- `400`: missing required columns
- `400`: malformed CSV rows

### List users

`GET /users?page=1&per_page=10`

Query constraints:

- `page >= 1`
- `1 <= per_page <= 100`

Success: `200 OK`, array of users.

### Get user

`GET /users/{id}`

- `200`: user JSON
- `404`: `{"detail": "User not found"}`

### Update user

`PUT /users/{id}`

Request body:

```json
{"username": "alice-updated"}
```

- `200`: updated user
- `400`: username already registered
- `404`: user not found

### Delete user

`DELETE /users/{id}`

Behavior:

- Deletes user
- Deletes all user URLs
- Deletes all related URL/user events

Response: `204 No Content`

## URLs API

### Create URL

`POST /urls`

Request body:

```json
{
  "user_id": 1,
  "original_url": "https://example.com/page",
  "title": "Example Page"
}
```

Success: `201 Created`

- Generates a unique 6-char short code.
- Emits `created` event asynchronously.

Errors:

- `404`: owner user not found
- `422`: schema/type validation failure
- `503`: unique short code generation failed after retries

### List URLs

`GET /urls?skip=0&limit=100&user_id=1&is_active=true`

Filters:

- `user_id` (optional)
- `is_active` (optional)

Success: ordered list by URL id.

### Get URL by id

`GET /urls/{id}`

Behavior:

- Returns only active URLs.
- Emits `accessed` event asynchronously when found.

Errors:

- `404`: missing or inactive URL

### Redirect short code

`GET /urls/{short_code}/redirect`

Behavior:

- Returns `302 Found` with `Location` header
- Emits `click` event asynchronously

Errors:

- `404`: missing or inactive URL

### Update URL

`PUT /urls/{id}`

Request body examples:

```json
{"title": "New title"}
```

```json
{"is_active": false}
```

Behavior:

- Emits `updated` event asynchronously on success.

### Delete URL

`DELETE /urls/{id}`

Behavior:

- Deletes URL row
- Deletes associated events

Response: `204 No Content`

## Events API

### Create event

`POST /events`

Request body:

```json
{
  "url_id": 1,
  "user_id": 1,
  "event_type": "click",
  "details": {"referrer": "https://google.com"}
}
```

Errors:

- `404`: user not found
- `404`: URL not found

### List events

`GET /events?skip=0&limit=100&url_id=1&user_id=1&event_type=click`

Filters:

- `url_id`
- `user_id`
- `event_type`

Returns ordered history by event id.
