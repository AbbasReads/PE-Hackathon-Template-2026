# Track 3: Scalability and Monitoring

## What this track covers

Track 3 documents horizontal scaling, load balancing, load-test methodology, and production-style monitoring/alerting.

Implemented artifacts in repository:

- Multi-instance app deployment through Docker Compose
- NGINX reverse proxy and load balancing
- K6 load testing scripts for bronze and silver intensity
- Prometheus scraping and alert rules
- Alertmanager routing for critical and warning alerts
- Alert test helper script

## Key files

- `compose.yaml`
- `nginx/nginx.conf`
- `loadtest_bronze.js`
- `loadtest_silver.js`
- `monitoring/prometheus/prometheus.yml`
- `monitoring/prometheus/alert_rules.yml`
- `monitoring/alertmanager/alertmanager.yml`
- `scripts/test_alerts.sh`

## Track outcomes

- Increased throughput capacity using more than one app instance
- Stable endpoint behavior under synthetic mixed workload
- Monitoring stack for service health and error-rate alerts

## Important configuration note

`compose.yaml` currently contains two `services` blocks. In YAML, duplicate top-level keys can cause earlier blocks to be overwritten depending on parser behavior. For predictable deployments, keep one canonical service block before production use.

## Related pages

- `load-testing.md`
- `monitoring-and-alerting.md`
- `operations-playbook.md`
- `diagrams.md`
