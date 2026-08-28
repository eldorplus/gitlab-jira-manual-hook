# AGENTS.md

## Purpose
`gitlab-jira-manual-hook` receives GitLab Job Webhooks and creates Jira issues for approved jobs waiting in `manual` status.

## Rules
- Keep GitLab parsing, policy, idempotency and Jira integration separated.
- Authenticate the webhook before processing payloads.
- Project policy is fail-closed.
- Never log webhook secrets or Jira API tokens.
- Never create duplicate issues for the same `(project_id, pipeline_id, job_id)`.
- Jira failures mark the action failed and return a non-success response so GitLab can retry.

## Development
Python 3.12+, FastAPI, asyncpg, httpx and pytest. Run `make test` before submitting changes.
