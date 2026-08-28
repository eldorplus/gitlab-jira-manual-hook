# AGENTS.md

## Purpose
`gitlab-jira-manual-hook` receives GitLab Job and Pipeline Webhooks. It creates Jira issues for explicitly approved jobs waiting in `manual` status and publishes GitLab CI observability events to Elasticsearch/Kibana.

## Architecture rules
- Keep GitLab parsing, policy, idempotency, Jira and Elasticsearch integrations separated.
- Keep webhook authentication before payload processing.
- Job webhook: `/webhook/gitlab`.
- Pipeline webhook: `/webhook/gitlab/pipeline`.
- Project policy is always fail-closed; never default a project to enabled.
- Elasticsearch observability is best-effort and must never prevent the GitLab → Jira path from completing.
- Do not expose secrets in logs, Elasticsearch documents or error messages.
- Never create duplicate Jira issues for the same `(project_id, pipeline_id, job_id)`.
- Jira failures must be recorded as failed and return a retryable non-success response.

## Elasticsearch rules
- Use the asynchronous official Python client: `elasticsearch[async]` / `AsyncElasticsearch`.
- Default index pattern is `gitlab-pipelines-YYYY.MM.DD`.
- Use `@timestamp` as the canonical event timestamp.
- Keep GitLab fields under the `gitlab.*` namespace and ECS-compatible event fields under `event.*` where practical.
- Preserve pipeline status, ref, commit SHA, source, timing data and failure reason.
- Preserve optional jobs, stages, environment and runner metadata when GitLab supplies them.
- Elasticsearch connectivity errors must be logged without failing the webhook.

## Configuration
- Runtime configuration comes from environment variables / secret stores.
- `ELASTICSEARCH_ENABLED` controls observability.
- `ELASTICSEARCH_URL`, `ELASTICSEARCH_API_KEY` and `ELASTICSEARCH_INDEX_PREFIX` configure the Elasticsearch target.
- Never commit real `.env` files, Jira credentials, webhook tokens or Elasticsearch API keys.
- Kubernetes example secrets contain placeholders only.

## Testing
Python 3.12+, FastAPI, asyncpg, httpx, PyYAML, Elasticsearch async client and pytest.

Before submitting changes:

```bash
make test
```

Tests must cover authentication, fail-closed policy, idempotency, Jira failures/retries and Elasticsearch publishing. Elasticsearch should be mocked in unit tests; tests must not require a live cluster.

## Documentation
Keep `README.md` and the documents under `docs/` synchronized with API endpoints, configuration, deployment and observability behavior.

## Changes
- Prefer small, focused commits.
- Do not mix secrets or environment-specific production values into source-controlled configuration.
- Update fixtures and tests when GitLab webhook payload assumptions change.
