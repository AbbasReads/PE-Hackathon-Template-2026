# Track 2 Diagrams

This page contains reliability-focused diagrams: error handling, recovery, and observability loops.

## 1. Error Handling Decision Flow

```mermaid
flowchart TD
  Req[Incoming request] --> Val{Schema valid?}
  Val -- No --> E422[Return 422]
  Val -- Yes --> Logic{Business rule passes?}
  Logic -- No --> E4xx[Return 400 or 404]
  Logic -- Yes --> Exec[Execute route logic]
  Exec --> Crash{Unhandled exception?}
  Crash -- Yes --> E500[Global handler returns 500 JSON]
  Crash -- No --> Ok[Return success response]
```

## 2. Process Recovery Loop

```mermaid
flowchart TD
  Start[Container starts] --> Entrypoint[docker-entrypoint.sh]
  Entrypoint --> Uvicorn[Start uvicorn]
  Uvicorn --> Run[App serves traffic]
  Run --> Exit{Process exits unexpectedly?}
  Exit -- No --> Run
  Exit -- Yes --> Sleep[Wait 1 second]
  Sleep --> Restart[Restart uvicorn]
  Restart --> Run
```

## 3. Reliability Observability Feedback Loop

```mermaid
flowchart LR
  Traffic[Client traffic] --> App[FastAPI App]
  App --> Logs[Structured JSON Logs]
  App --> Metrics[Metrics and diagnostics]
  Logs --> Detect[Detection and diagnosis]
  Metrics --> Detect
  Detect --> Action[Mitigation and recovery]
  Action --> App
```

## 4. Dependency Health Startup Flow

```mermaid
sequenceDiagram
  participant D as PostgreSQL
  participant C as Docker Compose
  participant A as App Service

  C->>D: Start database container
  D-->>C: Healthcheck passes (pg_isready)
  C->>A: Start app service
  A->>D: Initialize metadata and session pool
  D-->>A: Ready for queries
  A-->>C: Application healthy
```
