# Track 1: Core Service Foundations

## Who this section is for

If you are new to this repository, start here. This section explains what the API does, how the data model is organized, and how requests flow through the system.

## What this track delivers

Track 1 establishes the application's functional backbone:

- User management (create, list, update, delete, bulk CSV import)
- URL management (create, list, fetch, update, delete, redirect)
- Event history (automatic event creation and explicit event APIs)
- Input validation and strongly typed request/response schemas

## System boundaries

This service is a URL shortener and event tracker built with FastAPI + SQLAlchemy + PostgreSQL.

Core runtime pieces:

- API application factory in `app/__init__.py`
- Runtime bootstrapping in `run.py`
- Database engine and session provider in `app/database.py`
- Domain models in `app/models/domain.py`
- API schemas in `app/models/schemas.py`
- Route modules in `app/routes/`

## Request lifecycle

1. HTTP request enters FastAPI app.
2. Pydantic schema validation runs before route execution.
3. Route handler resolves dependencies (DB session, background tasks).
4. SQLAlchemy operations read/write PostgreSQL records.
5. Response model serialization returns consistent JSON output.
6. Request middleware logs timing/status metadata.

## API domains

### Users

- `POST /users`: create single user
- `GET /users`: paginated user list
- `GET /users/{id}`: get user by id
- `PUT /users/{id}`: update username
- `DELETE /users/{id}`: delete user and related URLs/events
- `POST /users/bulk`: CSV bulk import with validation/dedupe rules

### URLs

- `POST /urls`: create short URL
- `GET /urls`: list URLs with optional filters (`user_id`, `is_active`)
- `GET /urls/{id}`: get URL by numeric id (only active URLs)
- `PUT /urls/{id}`: update title and/or active flag
- `DELETE /urls/{id}`: delete URL and related events
- `GET /urls/{short_code}/redirect`: 302 redirect to original URL and log click event

### Events

- `POST /events`: create event explicitly
- `GET /events`: list events with optional filters (`url_id`, `user_id`, `event_type`)

## Data model summary

### users

- Primary key: `id`
- Unique fields: `email`
- Indexed fields: `id`, `username`, `email`

### urls

- Primary key: `id`
- Foreign key: `user_id -> users.id`
- Unique fields: `short_code`
- Status field: `is_active`

### events

- Primary key: `id`
- Foreign keys: `url_id -> urls.id`, `user_id -> users.id`
- Event payload: JSON field `details`

## Seed data and startup behavior

The app can auto-seed from `seed_data/` on startup when:

- `ENABLE_STARTUP_SEED=true`

Seeding is skipped if users already exist.

## Related pages

- `api-reference.md`
- `data-model-and-validation.md`
- `developer-workflow.md`
- `diagrams.md`
