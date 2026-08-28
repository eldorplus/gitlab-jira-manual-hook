# GitLab Jira Manual Hook

Webhook service that creates a Jira issue when a GitLab CI job enters `manual` status.

## Status

Initial project bootstrap.

## Architecture

GitLab Job Webhook → FastAPI → PostgreSQL idempotency → Jira REST API.

## Planned features

- GitLab Job Hook validation with `X-Gitlab-Token`
- filtering by project, stage and job
- Jira REST API v3 issue creation
- PostgreSQL idempotency
- retries and structured logging
- Docker Compose
- Kubernetes manifests
- automated tests
- optional Jira → GitLab manual job play action
