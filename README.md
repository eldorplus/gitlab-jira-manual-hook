# GitLab Jira Manual Hook

FastAPI webhook service that creates a Jira issue when a GitLab CI job enters `manual` status.

## Architecture

```text
GitLab Job Webhook -> FastAPI -> Policy -> PostgreSQL idempotency -> Jira REST API
```

## Features (V1)

- GitLab Job Hook (`object_kind=build`) and `build_status=manual` detection
- `X-Gitlab-Token` validation
- fail-closed project/stage/job policy
- PostgreSQL idempotency using `(project_id, pipeline_id, job_id)`
- Jira REST API v3 / ADF description
- Jira retries with exponential backoff
- structured application logging
- Docker and Docker Compose
- PostgreSQL schema initialization
- pytest test suite
- GitHub Actions CI and Docker build
- health endpoint

## Configuration

Copy `.env.example` to `.env` and set at least:

```text
WEBHOOK_SECRET=<random-secret>
JIRA_BASE_URL=https://your-domain.atlassian.net
JIRA_EMAIL=automation@example.com
JIRA_API_TOKEN=<token>
JIRA_PROJECT_KEY=OPS
JIRA_ISSUE_TYPE=Task
DATABASE_URL=postgresql://manualhook:manualhook@postgres:5432/manualhook
```

Configure projects in `config/projects.yml`. Production is opt-in: projects must be explicitly enabled.

## GitLab Webhook

In GitLab project/group settings, add a webhook targeting:

```text
POST /webhook/gitlab
```

Enable **Job events** and use the same signing token as `WEBHOOK_SECRET`.

## Local development

```bash
cp .env.example .env
make compose-up
curl http://localhost:8000/health
make test
```

## Security notes

Never commit Jira API tokens or the GitLab webhook secret. Put secrets in the deployment secret store. The policy is intentionally fail-closed so an unconfigured project cannot generate Jira tickets.

## Future V2

- Jira action to play a GitLab manual job
- asynchronous queue/worker
- dead-letter handling
- metrics and tracing
- Jira custom fields and templates
