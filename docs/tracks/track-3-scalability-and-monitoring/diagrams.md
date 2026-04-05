# Track 3 Diagrams

This page visualizes scale-out architecture, load testing progression, and monitoring pipelines.

## 1. Horizontal Scaling Architecture

```mermaid
flowchart LR
  U[Users] --> N[NGINX Load Balancer]
  N --> A1[App Instance 1]
  N --> A2[App Instance 2]
  N --> A3[App Instance 3]
  A1 --> DB[(PostgreSQL)]
  A2 --> DB
  A3 --> DB
```

## 2. Monitoring and Alert Pipeline

```mermaid
flowchart LR
  App[App /metrics endpoint] --> Prom[Prometheus]
  Prom --> Rules[Alert Rule Evaluation]
  Rules --> AM[Alertmanager]
  AM --> S[Slack Notifications]
  AM --> D[Discord Notifications]
```

## 3. Load Test Stage Timeline

```mermaid
gantt
  title k6 Load Profile Comparison
  dateFormat X
  axisFormat %Ls
  section Bronze
  Ramp up to 50 VUs :b1, 0, 10
  Hold 50 VUs :b2, 10, 20
  Ramp down :b3, 30, 5
  section Silver
  Ramp up to 200 VUs :s1, 0, 10
  Hold 200 VUs :s2, 10, 20
  Ramp down :s3, 30, 5
```

## 4. Request Path Through Load Balancer

```mermaid
sequenceDiagram
  participant Client
  participant NGINX
  participant App as App Replica
  participant DB as PostgreSQL

  Client->>NGINX: HTTP request
  NGINX->>App: Forward request (round robin)
  App->>DB: Execute query/mutation
  DB-->>App: Data
  App-->>NGINX: HTTP response
  NGINX-->>Client: Response
```
