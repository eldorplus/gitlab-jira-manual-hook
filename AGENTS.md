# AGENTS.md

## Purpose
`gitlab-jira-manual-hook` receives GitLab Job and Pipeline Webhooks. Approved manual jobs are persisted idempotently, queued durably in PostgreSQL and processed by a worker that creates/synchronizes Jira issues. Pipeline events are observed in Elasticsearch/Kibana. OpenTelemetry provides traces and metrics.

## Architecture rules
- Keep GitLab parsing, policy, idempotency, queue, Jira, Elasticsearch and telemetry separated.
- Authenticate webhooks before payload processing.
- Job webhook: `/webhook/gitlab`.
- Pipeline webhook: `/webhook/gitlab/pipeline`.
- Project policy is always fail-closed.
- Approved Jira work is asynchronous when `QUEUE_ENABLED=true`; the API must not wait for Jira.
- Queue data is durable in PostgreSQL. Workers use `FOR UPDATE SKIP LOCKED` and a visibility timeout.
- Failed queue items use exponential retry and move to `webhook_dead_letters` after `WORKER_MAX_ATTEMPTS`.
- Dead-letter requeue must reset the attempt count and preserve the original payload.
- Never create duplicate Jira issues for the same `(project_id, pipeline_id, job_id)`.
- If an idempotency record already contains a Jira issue key, synchronize that issue instead of creating another.
- Elasticsearch remains best-effort and must never block the webhook.
- Do not expose secrets in logs, traces, metrics attributes, Elasticsearch documents or error messages.

## Jira synchronization
- Use Jira REST API v3 and Atlassian Document Format for rich text.
- Keep GitLab project, pipeline, job, stage, ref and commit information synchronized.
- Retry transient HTTP failures with bounded exponential backoff.
- Instrument create/update operations with OpenTelemetry.

## Elasticsearch rules
- Use `elasticsearch[async]` / `AsyncElasticsearch`.
- Default index pattern is `gitlab-pipelines-YYYY.MM.DD`.
- Use `@timestamp` as the canonical event timestamp.
- Keep GitLab fields under `gitlab.*` and ECS-compatible fields under `event.*` where practical.
- Preserve status, ref, SHA, source, timings, failure reason and optional jobs/stages/environment/runner metadata.

## OpenTelemetry
- Use `OTEL_ENABLED` as the feature flag.
- Export traces and metrics using OTLP.
- Service name comes from `OTEL_SERVICE_NAME`.
- Endpoint comes from `OTEL_EXPORTER_OTLP_ENDPOINT`.
- Do not put credentials or sensitive payloads in span attributes.

## Kubernetes
- Application and worker are separate Deployments.
- PostgreSQL runs separately as `postgres:17-alpine` in a StatefulSet with persistent storage.
- Never put production secrets in source-controlled manifests.

## Testing
Python 3.12+, FastAPI, asyncpg, httpx, PyYAML, Elasticsearch async client, OpenTelemetry and pytest.

Before submitting changes:

```bash
make test
```

Unit tests must mock Elasticsearch, Jira and PostgreSQL boundaries. Add tests for queue retry/DLQ, Jira synchronization and telemetry instrumentation without requiring external services.

## Documentation
Keep `README.md` and all `docs/` files synchronized with endpoints, configuration, deployment, queue/DLQ, Jira synchronization, Elasticsearch and OpenTelemetry behavior.

## Changes
- Prefer small, focused commits.
- Do not commit credentials, `.env`, real Kubernetes Secrets or environment-specific production values.
- Update fixtures and tests whenever GitLab webhook payload assumptions change.
