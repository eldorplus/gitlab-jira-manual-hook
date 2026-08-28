# GitLab Jira Manual Hook

FastAPI service integrating GitLab CI, Jira and Elasticsearch/Kibana, with durable asynchronous processing and OpenTelemetry.

## What it does

1. Receives GitLab Job Hook events and detects jobs in `manual` status.
2. Applies an explicit fail-closed project/stage/job policy.
3. Records idempotency in PostgreSQL.
4. Enqueues approved Jira work in a durable PostgreSQL queue.
5. A dedicated worker creates or synchronizes Jira issues with retries and dead-letter handling.
6. Receives GitLab Pipeline Hook events and publishes observability data to Elasticsearch.
7. Exposes traces and metrics through OpenTelemetry/OTLP.
8. Provides versioned Kibana saved-object assets and an automated import script.

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
```

Elasticsearch is best-effort. Jira processing is decoupled from the webhook request through the durable queue.

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
- Docker / Docker Compose
- Kubernetes Deployment + dedicated worker + PostgreSQL StatefulSet/PVC
- pytest tests
- GitHub Actions CI and Docker image build
- `/health` and `/ready` endpoints

## Repository layout

```text
app/
├── api/
│   ├── pipeline_webhook.py
│   └── webhook.py
├── repositories/
│   ├── manual_action_repository.py
│   └── queue_repository.py
├── services/
│   ├── dead_letter_service.py
│   ├── elastic_service.py
│   ├── gitlab_service.py
│   ├── idempotency_service.py
│   ├── jira_service.py
│   ├── pipeline_observability_service.py
│   ├── policy_service.py
│   ├── telemetry.py
│   └── webhook_service.py
└── worker.py

deploy/
├── kibana/
│   ├── data-view.json
│   ├── gitlab-pipelines.ndjson
│   └── import.sh
└── kubernetes/
    ├── deployment.yaml
    ├── worker-deployment.yaml
    ├── postgres.yaml
    └── ...

docs/
├── configuration.md
├── usage.md
└── observability.md
```

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

## GitLab Webhooks

Configure:

- **Job events** → `POST /webhook/gitlab`
- **Pipeline events** → `POST /webhook/gitlab/pipeline`

Use `WEBHOOK_SECRET` as the GitLab secret token.

## Local development

```bash
cp .env.example .env
make compose-up
make test
uv run gitlab-jira-worker
```

The worker can also be started with the installed `gitlab-jira-worker` entrypoint.

## Kubernetes

```bash
kubectl apply -f deploy/kubernetes/namespace.yaml
kubectl apply -f deploy/kubernetes/configmap.yaml
kubectl apply -f deploy/kubernetes/secret.example.yaml
kubectl apply -f deploy/kubernetes/elasticsearch-configmap.yaml
kubectl apply -f deploy/kubernetes/elasticsearch-secret.example.yaml
kubectl apply -f deploy/kubernetes/postgres.yaml
kubectl apply -f deploy/kubernetes/deployment.yaml
kubectl apply -f deploy/kubernetes/worker-deployment.yaml
kubectl apply -f deploy/kubernetes/service.yaml
kubectl apply -f deploy/kubernetes/ingress.yaml
```

PostgreSQL is isolated in a StatefulSet and persists through a PVC. Replace example secrets and hostnames before production.

## Kibana assets

Import the versioned assets:

```bash
cd deploy/kibana
KIBANA_URL=https://kibana.example.com KIBANA_API_KEY=... ./import.sh
```

The Data View is `gitlab-pipelines-*` with `@timestamp` as the time field.

## Security

Secrets must come from environment variables or a deployment secret store. Never commit Jira tokens, Elasticsearch API keys, webhook secrets or real Kubernetes Secrets. Policy remains deny-by-default.

## Documentation

- `docs/usage.md` — installation, webhooks, worker and operations
- `docs/configuration.md` — environment, queue, Jira, Elasticsearch and OpenTelemetry configuration
- `docs/observability.md` — telemetry schema, OTLP and Kibana dashboards

## Status

The V1 roadmap is implemented: asynchronous queue/worker, dead-letter handling, OpenTelemetry metrics/tracing, richer Jira synchronization and automated Kibana assets.
