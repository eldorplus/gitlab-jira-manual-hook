# GitLab Jira Manual Hook

FastAPI service integrating GitLab CI, Jira and Elasticsearch/Kibana, with durable asynchronous processing, versioned PostgreSQL migrations and OpenTelemetry.

## What it does

1. Receives GitLab Job Hook events and detects jobs in `manual` status.
2. Applies an explicit fail-closed project/stage/job policy.
3. Records idempotency in PostgreSQL.
4. Enqueues approved Jira work in a durable PostgreSQL queue.
5. A dedicated worker creates or synchronizes Jira issues with retries and dead-letter handling.
6. Receives GitLab Pipeline Hook events and publishes observability data to Elasticsearch.
7. Exposes traces and metrics through OpenTelemetry/OTLP.
8. Provides versioned Kibana saved-object assets and an automated import script.
9. Manages schema changes with versioned Alembic migrations.

## Architecture

```text
GitLab
 ├─ Job Hook ──> API ──> Policy ──> Idempotency ──> PostgreSQL Queue ──> Worker ──> Jira
 │                                                   │                    │
 │                                                   └── DLQ              └── retry
 │
 └─ Pipeline Hook ──> API ──> Elasticsearch ──> Kibana
                         │
                         └── OpenTelemetry ──> OTLP Collector

PostgreSQL ──> StatefulSet + volumeClaimTemplates (Kubernetes)
```

## Features

- GitLab Job and Pipeline Webhooks
- `X-Gitlab-Token` authentication
- fail-closed project/stage/job policy
- PostgreSQL idempotency on `(project_id, pipeline_id, job_id)`
- durable PostgreSQL async queue
- dedicated worker process
- exponential retry with configurable maximum attempts
- dead-letter queue and requeue service
- Jira REST API v3 with ADF descriptions
- Jira issue create/update synchronization
- asynchronous `elasticsearch[async]` client
- daily `gitlab-pipelines-YYYY.MM.DD` indexes
- pipeline status, ref, SHA, source, timings and failure reason
- optional jobs, stages, environment and runner metadata
- OpenTelemetry traces and OTLP metrics
- automated Kibana Data View and dashboard assets
- Alembic versioned database migrations
- PostgreSQL 17 StatefulSet with persistent `volumeClaimTemplates`
- Docker / Docker Compose
- Kubernetes Deployment + dedicated worker + PostgreSQL StatefulSet/PVC
- pytest tests
- GitHub Actions CI and Docker image build
- `/health` and `/ready` endpoints

## Database migrations

Install dependencies and configure `DATABASE_URL`, then run:

```bash
alembic upgrade head
```

Create a migration:

```bash
alembic revision -m "describe change"
```

Migrations are stored under `alembic/versions/`. Run migrations as a controlled deployment step before rolling out API/worker replicas; do not run schema creation independently in every application replica.

## Configuration

Copy `.env.example` to `.env`.

### Queue

```dotenv
QUEUE_ENABLED=true
WORKER_POLL_INTERVAL=2
WORKER_BATCH_SIZE=10
WORKER_MAX_ATTEMPTS=5
WORKER_RETRY_BASE_SECONDS=2
```

### Elasticsearch

```dotenv
ELASTICSEARCH_ENABLED=true
ELASTICSEARCH_URL=https://elasticsearch.example.com:443
ELASTICSEARCH_API_KEY=replace-me
ELASTICSEARCH_INDEX_PREFIX=gitlab-pipelines
```

### OpenTelemetry

```dotenv
OTEL_ENABLED=true
OTEL_SERVICE_NAME=gitlab-jira-manual-hook
OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317
OTEL_INSECURE=true
```

## Kubernetes

```bash
kubectl apply -f deploy/kubernetes/namespace.yaml
kubectl apply -f deploy/kubernetes/configmap.yaml
kubectl apply -f deploy/kubernetes/secret.example.yaml
kubectl apply -f deploy/kubernetes/elasticsearch-configmap.yaml
kubectl apply -f deploy/kubernetes/elasticsearch-secret.example.yaml
kubectl apply -f deploy/kubernetes/postgres.yaml
# Run Alembic upgrade head as a controlled migration step here.
kubectl apply -f deploy/kubernetes/deployment.yaml
kubectl apply -f deploy/kubernetes/worker-deployment.yaml
kubectl apply -f deploy/kubernetes/service.yaml
kubectl apply -f deploy/kubernetes/ingress.yaml
```

PostgreSQL is isolated in a StatefulSet. Its storage is created through `volumeClaimTemplates`, giving `postgres-0` a persistent `postgres-data-postgres-0` claim.

## Documentation

- `docs/usage.md` — installation, webhooks, worker and operations
- `docs/configuration.md` — environment, queue, Jira, Elasticsearch and OpenTelemetry configuration
- `docs/observability.md` — telemetry schema, OTLP and Kibana dashboards
- `docs/queue-worker.md` — queue, retry, DLQ, migrations and PostgreSQL persistence
- `docs/jira-synchronization.md` — Jira create/update lifecycle

## Status

The V1 roadmap is implemented: asynchronous queue/worker, dead-letter handling, OpenTelemetry metrics/tracing, richer Jira synchronization, automated Kibana assets, versioned Alembic migrations and persistent Kubernetes PostgreSQL storage.
