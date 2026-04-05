# Track 3 Monitoring and Alerting

## Monitoring stack components

### Prometheus

Configured in `monitoring/prometheus/prometheus.yml`.

Responsibilities:

- scrape app metrics from `/metrics`
- evaluate alert rules every 15 seconds
- forward firing alerts to Alertmanager

### Alert rules

Defined in `monitoring/prometheus/alert_rules.yml`.

Current rules:

- `ServiceDown` (critical): app unreachable for 2 minutes
- `HighErrorRate` (critical): 5xx ratio over 5%
- `HighCPU` (warning): CPU usage over 90% for 2 minutes

### Alertmanager

Configured in `monitoring/alertmanager/alertmanager.yml`.

Responsibilities:

- route critical alerts to on-call channel
- route warnings to non-paging channel
- inhibit noisy secondary alerts (e.g., suppress `HighErrorRate` when `ServiceDown` is active)

## Metrics exposure

The app exposes Prometheus metrics via instrumentation middleware when optional dependencies are available.

Required Python packages for `/metrics` exposure:

- `prometheus-fastapi-instrumentator`
- `prometheus_client`

If these packages are missing, Prometheus scrape on `/metrics` will fail and only JSON diagnostics endpoint `/metrics/json` remains available.

Additional JSON diagnostics endpoint exists at:

- `GET /metrics/json`

## Notification channels

Environment-driven webhook substitution supports:

- Slack
- Discord (Slack-compatible webhook endpoint)

Runtime environment variables used in compose:

- `SLACK_WEBHOOK_URL`
- `DISCORD_WEBHOOK_URL`

## Validating alerts

Use helper script:

```bash
./scripts/test_alerts.sh service-down
./scripts/test_alerts.sh errors
./scripts/test_alerts.sh cpu
```

This script supports synthetic alert conditions for end-to-end notification testing.

## Production hardening recommendations

1. Pin image versions for Prometheus and Alertmanager (avoid `latest`).
2. Add authentication for Prometheus/Alertmanager UIs.
3. Add persistent dashboarding (Grafana) for trend analysis.
4. Store alert runbook links in alert annotations.
