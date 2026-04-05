# Failure Modes

## Bad input

- Invalid request bodies return JSON validation errors with `422 Unprocessable Entity`.
- Unsupported file uploads return JSON `400` responses such as `{"detail": "Only CSV files allowed"}`.
- Missing resources return JSON `404` responses such as `{"detail": "User not found"}` or `{"detail": "URL not found"}`.

## Unexpected server errors

- Unhandled exceptions are converted into `500 Internal Server Error` with the JSON body `{"detail": "Internal Server Error"}`.
- This prevents stack traces from leaking to API clients.

## Container crashes

- Services in [compose.yaml](../compose.yaml) use `restart: unless-stopped`.
- App services are `app-1`, `app-2`, and `app-3`, plus `db`, `nginx`, `prometheus`, and `alertmanager`.
- With `unless-stopped`, manually killing/stopping a container is treated as an explicit stop and it will not auto-restart on its own.
- The app image entrypoint still provides process-level recovery inside a running container: if the `uvicorn` process dies, it is started again.

## Chaos demo

1. Start the stack:
   `docker compose up -d --force-recreate`
2. Confirm services are running:
   `docker compose ps`
3. Kill one app container (example: app-1):
   `docker kill pe-hackathon-template-2026-app-1-1`
4. Observe `app-1` is no longer running (expected under `unless-stopped`):
   `docker compose ps`
5. Bring app-1 back:
   `docker compose up -d app-1`
6. Kill only the in-container app process (`uvicorn`) to test process-level auto-recovery:
   `docker compose exec app-1 python -c "import os,signal; [os.kill(int(pid), signal.SIGKILL) for pid in os.listdir('/proc') if pid.isdigit() and pid != '1' and b'uvicorn' in open(f'/proc/{pid}/cmdline', 'rb').read()]"`
7. Watch logs show restart (`Killed`, then startup lines):
   `docker compose logs --tail=80 app-1`
8. Confirm service availability through the load balancer:
   `docker compose ps`
   `curl -i http://127.0.0.1:8000/health`

## Commands used to test

The following commands were used to validate restart behavior manually:

1. `docker compose up -d --force-recreate`
2. `docker compose ps`
3. `docker kill pe-hackathon-template-2026-app-1-1`
4. `docker compose ps`
5. `docker compose up -d app-1`
6. `docker compose exec app-1 python -c "import os,signal; [os.kill(int(pid), signal.SIGKILL) for pid in os.listdir('/proc') if pid.isdigit() and pid != '1' and b'uvicorn' in open(f'/proc/{pid}/cmdline', 'rb').read()]"`
7. `docker compose logs --tail=80 app-1`
8. `docker compose ps`
9. `curl -i http://127.0.0.1:8000/health`

Expected result:

- After `docker kill ...app-1-1`, `app-1` exits and stays stopped until manually started again.
- After killing `uvicorn` inside `app-1`, logs show restart and health remains reachable through `nginx` on port `8000`.
