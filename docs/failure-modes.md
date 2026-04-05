# Failure Modes

## Bad input

- Invalid request bodies return JSON validation errors with `422 Unprocessable Entity`.
- Unsupported file uploads return JSON `400` responses such as `{"detail": "Only CSV files allowed"}`.
- Missing resources return JSON `404` responses such as `{"detail": "User not found"}` or `{"detail": "URL not found"}`.

## Unexpected server errors

- Unhandled exceptions are converted into `500 Internal Server Error` with the JSON body `{"detail": "Internal Server Error"}`.
- This prevents stack traces from leaking to API clients.

## Container crashes

- The `app` and `db` services in [compose.yaml](../compose.yaml) use `restart: unless-stopped`.
- The app container also runs through a tiny supervisor script in [docker-entrypoint.sh](../docker-entrypoint.sh), so if the web process crashes, it is started again automatically inside the container.

## Chaos demo

1. Start the stack:
   `docker compose up -d --build`
2. Confirm both services are running:
   `docker compose ps`
3. Crash the web process inside the app container:
   `docker exec hackathon-app python -c "import os, signal; [os.kill(int(pid), signal.SIGKILL) for pid in os.listdir('/proc') if pid.isdigit() and pid != '1' and b'uvicorn' in open(f'/proc/{pid}/cmdline', 'rb').read()]" `
4. Watch the supervisor bring it back:
   `docker compose logs app`
5. Confirm the service stays available:
   `docker compose ps`
   `curl http://127.0.0.1:8080/health`
