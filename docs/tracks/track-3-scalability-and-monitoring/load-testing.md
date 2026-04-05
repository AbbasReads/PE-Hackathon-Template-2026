# Track 3 Load Testing Guide

## Objective

Measure behavior under realistic mixed traffic and compare scaling profiles.

## Scripts

- `loadtest_bronze.js`: baseline profile (50 VUs)
- `loadtest_silver.js`: higher concurrency profile (200 VUs)

## Traffic model

Both scripts simulate mixed endpoint usage with weighted distribution:

- Heavy read pressure on `GET /urls`
- Secondary pressure on `GET /events`
- Moderate user reads
- Low write traffic on `POST /urls`
- Background health checks

This model approximates real product usage where reads dominate writes.

## Thresholds

Configured SLO-like thresholds in scripts:

- `http_req_duration p95 < 2000ms`
- `http_req_failed rate < 5%`

## How to run

1. Start stack:

```bash
docker compose up -d --build
```

2. Run Bronze:

```bash
k6 run loadtest_bronze.js
```

3. Run Silver:

```bash
k6 run loadtest_silver.js
```

4. Compare outputs:

- p95 latency
- failure rate
- throughput (`http_reqs`)

## Interpreting results

- If failure rate spikes first: inspect app logs and DB saturation symptoms.
- If p95 spikes without failures: likely CPU contention or slow DB queries.
- If errors cluster in write routes: inspect short-code generation collisions or DB write pressure.

## Evidence assets

Load-test screenshots are included under `screenshots/` for bronze/silver/gold submissions.
