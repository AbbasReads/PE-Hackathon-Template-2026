# Manual Alert Testing Runbook

This runbook provides step-by-step commands to manually test Prometheus and Alertmanager alerts in this project.

## Why alerts were repeating

Alert repeats were caused by an overly aggressive Alertmanager repeat setting.

Current notification timing in `monitoring/alertmanager/alertmanager.yml`:
- `group_wait: 5s` (fast first notification)
- `group_interval: 30s` (updates grouped changes no faster than every 30s)
- `repeat_interval: 30m` (same unresolved alert repeats every 30 minutes)

## Prerequisites

Run from project root:

```bash
cd /home/cryptosaiyan/Documents/PE-Hackathon-Template-2026
```

Ensure Docker and Docker Compose are available:

```bash
docker --version
docker compose version
```

## 1) Start or refresh stack

```bash
docker compose up -d --force-recreate
```

```bash
docker compose ps
```

## 2) Open dashboards

- Prometheus: http://localhost:9090
- Prometheus alerts page: http://localhost:9090/alerts
- Alertmanager: http://localhost:9093

Optional terminal watcher:

```bash
watch -n 2 "curl -s http://localhost:9090/api/v1/alerts"
```

## 3) Test AppInstanceDown (single replica down)

```bash
docker compose stop app-1
```

Wait about 10 to 20 seconds, then check:

```bash
curl -s http://localhost:9090/api/v1/alerts
```

Recover:

```bash
docker compose start app-1
```

## 4) Test ServiceFleetDown (all replicas down)

```bash
docker compose stop app-1 app-2 app-3
```

Wait about 10 to 20 seconds, then check:

```bash
curl -s http://localhost:9090/api/v1/alerts
```

Recover:

```bash
docker compose start app-1 app-2 app-3
```

## 5) Test LoadBalancerDown

```bash
docker compose stop nginx
```

Wait about 10 to 20 seconds, then check:

```bash
curl -s http://localhost:9090/api/v1/alerts
```

Recover:

```bash
docker compose start nginx
```

## 6) Test HighErrorRate

One reliable way is to force backend failures temporarily by stopping DB and generating API traffic.

```bash
docker compose stop db
```

Generate failing traffic (fish shell):

```fish
for i in (seq 1 150)
    curl -s -o /dev/null -X POST http://localhost:8000/users \
      -H "Content-Type: application/json" \
      -d '{"username":"u'$i'","email":"u'$i'@x.com"}' &
end
wait
```

Check alerts:

```bash
curl -s http://localhost:9090/api/v1/alerts
```

Recover DB:

```bash
docker compose start db
```

## 7) Test HighCPUReplica (optional)

Create CPU load in one app container:

```bash
docker compose exec app-1 sh -lc "yes > /dev/null"
```

In another terminal, check alerts:

```bash
curl -s http://localhost:9090/api/v1/alerts
```

Stop load with `Ctrl+C`.

## 8) Final recovery and verification

```bash
docker compose up -d
```

```bash
docker compose ps
```

```bash
curl -s http://localhost:9090/api/v1/alerts
```

## Notes

- With current settings, first notification is fast but repeated sends for the same unresolved alert are throttled to every 30 minutes.
- If alerts still feel noisy, increase `repeat_interval` further (for example, `1h`).
