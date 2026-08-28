# GitLab Jira Manual Hook

FastAPI service that integrates GitLab CI, Jira and Elasticsearch/Kibana.

## What it does

1. Receives GitLab **Job Hook** events and detects jobs in `manual` status.
2. Applies an explicit, fail-closed project/stage/job policy.
3. Uses PostgreSQL idempotency to prevent duplicate Jira issues.
4. Creates a Jira issue through REST API v3.
5. Receives GitLab **Pipeline Hook** events and publishes pipeline observability data to Elasticsearch for Kibana.

## Architecture

```text
GitLab
 ├─ Job Hook ────────────────> /webhook/gitlab ──> Policy ──> PostgreSQL ──> Jira
 │
 └─ Pipeline Hook ───────────> /webhook/gitlab/pipeline ──> Elasticsearch ──> Kibana
```

Elasticsearch is best-effort: its unavailability must not block GitLab → Jira processing.

## Features

- GitLab Job and Pipeline Webhooks
- `X-Gitlab-Token` authentication
- fail-closed project/stage/job policy
- PostgreSQL idempotency on `(project_id, pipeline_id, job_id)`
- Jira REST API v3 with ADF descriptions
- Jira retries with exponential backoff
- asynchronous `elasticsearch[async]` client
- daily `gitlab-pipelines-YYYY.MM.DD` indexes
- pipeline status, ref, SHA, source, timings and failure reason
- optional jobs, stages, environment and runner metadata
- Docker / Docker Compose
- Kubernetes manifests
- pytest tests
- GitHub Actions CI and Docker image build
- `/health` and `/ready` endpoints

## Repository layout

```text
app/
├── api/
│   ├── pipeline_webhook.py
│   └── webhook.py
├── services/
│   ├── elastic_service.py
│   ├── gitlab_service.py
│   ├── idempotency_service.py
│   ├── jira_service.py
│   ├── pipeline_observability_service.py
│   ├── policy_service.py
│   └── webhook_service.py
└── logging.py

deploy/
├── docker-compose.prod.yml
└── kubernetes/

docs/
├── configuration.md
├── usage.md
└── observability.md
```

## Configuration

Copy `.env.example` to `.env` and configure GitLab, Jira, PostgreSQL and, when required, Elasticsearch.

Important Elasticsearch variables:

```dotenv
ELASTICSEARCH_ENABLED=true
ELASTICSEARCH_URL=https://elasticsearch.example.com:443
ELASTICSEARCH_API_KEY=replace-me
ELASTICSEARCH_INDEX_PREFIX=gitlab-pipelines
```

Enable projects explicitly in `config/projects.yml`:

```yaml
projects:
  "12345":
    enabled: true
    stages: [deploy]
    jobs: [deploy_production]
```

## GitLab Webhooks

Configure two webhooks when both features are required:

- **Job events** → `POST /webhook/gitlab`
- **Pipeline events** → `POST /webhook/gitlab/pipeline`

Use the same webhook token as `WEBHOOK_SECRET`.

## Local development

```bash
cp .env.example .env
make compose-up
make test
curl http://localhost:8000/health
```

## Production

Docker Compose example:

```bash
docker compose -f deploy/docker-compose.prod.yml up -d
```

Kubernetes:

```bash
kubectl apply -f deploy/kubernetes/namespace.yaml
kubectl apply -f deploy/kubernetes/configmap.yaml
kubectl apply -f deploy/kubernetes/secret.example.yaml
kubectl apply -f deploy/kubernetes/elasticsearch-configmap.yaml
kubectl apply -f deploy/kubernetes/elasticsearch-secret.example.yaml
kubectl apply -f deploy/kubernetes/deployment.yaml
kubectl apply -f deploy/kubernetes/service.yaml
kubectl apply -f deploy/kubernetes/ingress.yaml
```

Replace all example secrets and hostnames before production deployment.

## Kibana

Create a Kibana Data View using:

```text
gitlab-pipelines-*
```

Use `@timestamp` as the time field. Recommended dashboards are described in `docs/observability.md`.

## Security

Secrets must come from environment variables or a deployment secret store. Never commit Jira API tokens, Elasticsearch API keys or GitLab webhook secrets. Policy remains deny-by-default.

## Documentation

- `docs/usage.md` — installation, GitLab webhooks and operations
- `docs/configuration.md` — environment variables and policy configuration
- `docs/observability.md` — Elasticsearch schema and Kibana dashboards

## Roadmap

Async queue/worker, dead-letter handling, OpenTelemetry metrics/tracing, richer Jira synchronization and automated Kibana assets.
