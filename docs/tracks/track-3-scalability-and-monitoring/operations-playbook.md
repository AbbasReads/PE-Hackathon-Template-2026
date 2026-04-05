# Track 3 Operations Playbook

## In Case of Emergency (Alert Fired)

Use this when any alert appears in Prometheus or Alertmanager.

### Goal

- Restore service first.
- Reduce user impact.
- Capture enough evidence for root-cause analysis.

### First 5 minutes checklist

1. Acknowledge the incident and assign one incident lead.
2. Confirm the alert is active:
	- Open http://localhost:9090/alerts
	- Open http://localhost:9093
3. Check end-user availability quickly:
	- curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8000/health
4. Check infrastructure state:
	- docker compose ps
5. Check recent app logs for errors:
	- docker compose logs --tail=200 app-1 app-2 app-3
6. Post a short status update (what fired, impact, current action).

### Alert-specific actions

#### AppInstanceDown

Symptoms:
- One app replica is unreachable.

Actions:
1. Identify failed container in docker compose ps.
2. Restart only the failed replica:
	- docker compose restart app-1
	- docker compose restart app-2
	- docker compose restart app-3
3. Verify Prometheus target recovers at http://localhost:9090/targets.
4. Confirm alert clears in http://localhost:9090/alerts.

Escalate when:
- Same replica fails repeatedly within 10 minutes.

#### ServiceFleetDown

Symptoms:
- All app replicas are unreachable.

Actions:
1. Verify load balancer and app containers:
	- docker compose ps
2. Bring up core services immediately:
	- docker compose up -d app-1 app-2 app-3 nginx
3. If app fails to start, verify DB is healthy:
	- docker compose ps db
	- docker compose logs --tail=200 db
4. Validate recovery:
	- curl -s http://localhost:8000/health
	- open http://localhost:9090/targets

Escalate when:
- Health endpoint remains unavailable for more than 5 minutes.

#### LoadBalancerDown

Symptoms:
- Nginx is unreachable.

Actions:
1. Restart load balancer:
	- docker compose restart nginx
2. Confirm container health:
	- docker compose ps nginx
3. Verify external path:
	- curl -I http://localhost:8000/health
4. Confirm backend targets are still healthy in Prometheus.

Escalate when:
- Nginx keeps restarting or upstreams are unreachable.

#### HighErrorRate

Symptoms:
- 5xx ratio is above threshold.

Actions:
1. Confirm current 5xx ratio:
	- curl -s --get 'http://localhost:9090/api/v1/query' --data-urlencode 'query=100 * (sum(rate(http_requests_total{job="url-shortener-apps",status=~"5.."}[5m])) or vector(0)) / clamp_min((sum(rate(http_requests_total{job="url-shortener-apps"}[5m])) or vector(0)), 1)'
2. Inspect app logs for stack traces:
	- docker compose logs --tail=300 app-1 app-2 app-3
3. Check DB connectivity and saturation symptoms.
4. If cause is unclear, perform safe mitigation:
	- restart one replica first, then re-check error rate
5. If persistent and user-impacting, roll back latest change or scale out replicas.

Escalate when:
- 5xx remains above threshold for more than 10 minutes after mitigation.

#### HighLatencyP95

Symptoms:
- p95 latency above threshold.

Actions:
1. Confirm p95 trend in Grafana and Prometheus.
2. Check CPU and memory pressure:
	- docker stats --no-stream
3. Reduce load if possible (pause heavy tests).
4. Scale app replicas if DB capacity allows.
5. Re-run silver load test to confirm improvement.

Escalate when:
- p95 remains above target with normal error rate after scaling.

#### HighCPUReplica

Symptoms:
- One replica CPU is sustained above threshold.

Actions:
1. Identify hot replica from alert labels.
2. Inspect per-container usage:
	- docker stats --no-stream app-1 app-2 app-3
3. Restart only the hot replica first.
4. If repeated, scale out and inspect expensive endpoints.

Escalate when:
- CPU returns to high state quickly after restart.

### Recovery verification checklist

1. All critical endpoints return healthy responses.
2. Prometheus targets show UP for app replicas and load balancer.
3. Alert state is resolved in Prometheus and Alertmanager.
4. Grafana panels for traffic, errors, latency, and CPU are stable.

### Communication template

- Incident: <alert name>
- Start time: <timestamp>
- Impact: <who/what was affected>
- Mitigation applied: <actions taken>
- Current status: <monitoring, recovered, degraded>
- Next update: <timestamp>

### After-action (within 24 hours)

1. Write root cause and trigger timeline.
2. Add one prevention action with owner and due date.
3. Update alert thresholds or runbook steps if needed.
4. Attach evidence (logs, metrics snapshots, relevant commands).

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
