# Track 3 Operations Playbook

## Daily operational checks

1. Verify container health:

```bash
docker compose ps
```

2. Verify app liveness:

```bash
curl http://localhost:8000/health
```

3. Verify metrics endpoint:

```bash
curl http://localhost:8000/metrics/json
```

4. Verify Prometheus target health:

- open `http://localhost:9090/targets`

5. Verify active alerts:

- open `http://localhost:9090/alerts`
- open `http://localhost:9093`

## Incident triage flow

1. Check if app is down or degraded.
2. Correlate alert type (`ServiceDown`, `HighErrorRate`, `HighCPU`).
3. Inspect app logs and request latency patterns.
4. Confirm DB health and connectivity.
5. Decide whether to scale out app replicas or restart affected services.

## Scale-out checklist

When increasing app replica count:

1. Ensure NGINX upstream points to the intended app service alias.
2. Confirm DB has enough connection capacity for extra workers.
3. Run silver load test and compare p95/error rate to baseline.
4. Observe alert noise after scaling changes.

## Post-incident template

- Incident start/end:
- Customer impact:
- Triggering signal:
- Root cause:
- Immediate remediation:
- Long-term prevention actions:
- Owner and due date:
