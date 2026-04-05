# Track 1 Data Model and Validation

## Why this page exists

This page explains how data is shaped and protected before it reaches the database.

## ORM models

Defined in `app/models/domain.py`.

### User

- `id`: integer PK
- `username`: string, indexed, required
- `email`: string, unique, indexed, required
- `created_at`: DB timestamp default

### URL

- `id`: integer PK
- `user_id`: FK to user
- `short_code`: unique string, indexed
- `original_url`: string
- `title`: string
- `is_active`: boolean, default true
- `created_at`: timestamp
- `updated_at`: timestamp with update hook

### Event

- `id`: integer PK
- `url_id`: FK to URL
- `user_id`: FK to user
- `event_type`: string
- `timestamp`: timestamp
- `details`: JSON payload

## API schema validation

Defined in `app/models/schemas.py`.

Validation highlights:

- `StrictStr` for string-only usernames/titles/event types
- `EmailStr` for user emails
- `HttpUrl` for URL creation
- Strict positive integers (`gt=0`) for IDs in write operations
- Whitespace stripping via Pydantic `str_strip_whitespace`

## CSV import validation rules

Implemented in `app/utils.py` and route-level logic in `app/routes/users.py`.

Validation pipeline:

1. File extension must be `.csv`
2. Content must decode as UTF-8
3. CSV must include `username` and `email` columns
4. Malformed rows are rejected (`ValueError`)
5. Duplicate emails are deduplicated case-insensitively
6. Invalid rows are skipped during bulk import

## Consistency behavior

- Email comparisons are normalized to lowercase.
- Username uniqueness is enforced for standard user creation.
- Bulk import can allow duplicate usernames only in seed-style CSV mode (`id` column present).

## Deletion semantics

Application-level cascades are handled in route logic:

- Deleting a user removes:
  - related URL rows
  - direct user events
  - URL events linked to those URLs
- Deleting a URL removes:
  - associated events

This keeps event and URL data consistent without requiring database-level cascade constraints in current scope.
