# GitLab Jira Manual Hook

FastAPI webhook service that creates a Jira issue when a GitLab CI job enters `manual` status.

## V1 architecture

GitLab Job Webhook → FastAPI → authentication → project policy → PostgreSQL idempotency → Jira REST API v3.

## V1 features

- GitLab Job Hook and `build_status=manual` detection
- `X-Gitlab-Token` authentication
- fail-closed project/stage/job policy
- PostgreSQL idempotency on `(project_id, pipeline_id, job_id)`
- Jira REST API v3 with ADF description
- retry with exponential backoff
- Docker / Docker Compose
- PostgreSQL initialization schema
- pytest tests
- GitHub Actions CI and Docker build
- health endpoint

## Configuration

Copy `.env.example` to `.env` and set `WEBHOOK_SECRET`, `JIRA_BASE_URL`, `JIRA_EMAIL`, `JIRA_API_TOKEN`, `JIRA_PROJECT_KEY`, `JIRA_ISSUE_TYPE` and `DATABASE_URL`.

Enable projects explicitly in `config/projects.yml`:

```yaml
projects:
  "12345":
    enabled: true
    stages: [deploy]
    jobs: [deploy_production]
```

## GitLab

Add a project or group webhook for `POST /webhook/gitlab`, enable **Job events**, and configure the same signing token as `WEBHOOK_SECRET`.

## Local

```bash
cp .env.example .env
make compose-up
curl http://localhost:8000/health
make test
```

## Security

Secrets must come from environment variables or a deployment secret store. Never commit Jira API tokens or GitLab webhook secrets. The default project policy is deny-by-default.

## V2 roadmap

Jira → GitLab `job/play`, asynchronous queue/worker, dead-letter handling, metrics/tracing, Jira custom fields/templates and richer lifecycle synchronization.
