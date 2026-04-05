# Track 1 Diagrams

This page provides architecture and flow diagrams for the Core Service Foundations track.

## 1. System Component Diagram

```mermaid
flowchart LR
  C[API Client] --> A[FastAPI Application]
  A --> U[Users Routes]
  A --> R[URLs Routes]
  A --> E[Events Routes]
  U --> DB[(PostgreSQL)]
  R --> DB
  E --> DB
  R --> BG[Background Tasks]
  BG --> DB
```

## 2. Request Lifecycle Sequence

```mermaid
sequenceDiagram
  participant C as Client
  participant A as FastAPI
  participant V as Pydantic Validation
  participant H as Route Handler
  participant S as SQLAlchemy Session
  participant P as PostgreSQL

  C->>A: HTTP request
  A->>V: Validate request body/query/path
  V-->>A: Valid or Invalid

  alt Valid request
    A->>H: Execute route function
    H->>S: Query or mutate data
    S->>P: Execute SQL
    P-->>S: Result set
    S-->>H: ORM objects
    H-->>A: Response object
    A-->>C: JSON response
  else Invalid request
    A-->>C: 422 validation error
  end
```

## 3. Data Model ER Diagram

```mermaid
erDiagram
  USERS ||--o{ URLS : owns
  USERS ||--o{ EVENTS : generates
  URLS ||--o{ EVENTS : records

  USERS {
    int id PK
    string username
    string email UK
    datetime created_at
  }

  URLS {
    int id PK
    int user_id FK
    string short_code UK
    string original_url
    string title
    boolean is_active
    datetime created_at
    datetime updated_at
  }

  EVENTS {
    int id PK
    int url_id FK
    int user_id FK
    string event_type
    text details
    datetime timestamp
  }
```

## 4. URL Redirect Event Flow

```mermaid
sequenceDiagram
  participant C as Client
  participant API as URLs Route
  participant DB as PostgreSQL
  participant BG as Background Task

  C->>API: GET /urls/{short_code}/redirect
  API->>DB: Find URL by short_code
  DB-->>API: URL record
  API-->>C: 302 Redirect to original_url
  API->>BG: Schedule click event write
  BG->>DB: INSERT event_type=click
```
