# Track 2: Reliability Engineering

## Goal

Track 2 ensures the service fails safely, recovers predictably, and remains diagnosable under stress or unexpected behavior.

## Reliability pillars implemented

- Error contract stability (`400/404/422/500` with JSON responses)
- Global exception handling to prevent sensitive error leakage
- DB connection pool hardening (`pool_pre_ping`, bounded pool/overflow)
- Health endpoint and middleware-level request telemetry
- Background event logging to keep request paths responsive
- Process-level restart loop in container entrypoint
- Container restart policies and healthchecks

## Why this matters for new team members

When you join the project, reliability docs tell you two critical things quickly:

1. What the system guarantees under failure.
2. How to diagnose and recover when those guarantees are breached.

## Reliability architecture at a glance

- API error normalization in `app/__init__.py`
- request and exception logging in `run.py`
- logging and metrics helpers in `app/observability.py`
- DB resilience settings in `app/database.py`
- process auto-restart in `docker-entrypoint.sh`

## Related pages

- `error-handling-contract.md`
- `resilience-and-recovery.md`
- `bonus-quest-report.md`
- `diagrams.md`
