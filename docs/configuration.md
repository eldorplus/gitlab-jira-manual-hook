# Configuration

## Variables d'environnement

| Variable | Défaut | Description |
|---|---|---|
| `WEBHOOK_SECRET` | `change-me` | Secret GitLab Webhook |
| `DATABASE_URL` | localhost | PostgreSQL |
| `JIRA_BASE_URL` | vide | Jira |
| `JIRA_EMAIL` | vide | compte API Jira |
| `JIRA_API_TOKEN` | vide | token Jira |
| `JIRA_PROJECT_KEY` | `OPS` | projet Jira par défaut |
| `JIRA_ISSUE_TYPE` | `Task` | type d'issue |
| `PROJECT_CONFIG` | `config/projects.yml` | policy YAML |
| `QUEUE_ENABLED` | `true` | active la queue durable |
| `WORKER_POLL_INTERVAL` | `2` | intervalle de polling en secondes |
| `WORKER_BATCH_SIZE` | `10` | taille de lot |
| `WORKER_MAX_ATTEMPTS` | `5` | maximum de tentatives |
| `WORKER_RETRY_BASE_SECONDS` | `2` | base du backoff exponentiel |
| `ELASTICSEARCH_ENABLED` | `false` | active Elasticsearch |
| `ELASTICSEARCH_URL` | vide | URL Elasticsearch |
| `ELASTICSEARCH_API_KEY` | vide | API key Elasticsearch |
| `ELASTICSEARCH_INDEX_PREFIX` | `gitlab-pipelines` | préfixe d'index |
| `OTEL_ENABLED` | `false` | active OpenTelemetry |
| `OTEL_SERVICE_NAME` | `gitlab-jira-manual-hook` | nom de service OTEL |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | `http://localhost:4317` | endpoint OTLP gRPC |
| `OTEL_INSECURE` | `true` | TLS OTLP |
| `LOG_LEVEL` | `INFO` | niveau de logs |

## Queue

```dotenv
QUEUE_ENABLED=true
WORKER_POLL_INTERVAL=2
WORKER_BATCH_SIZE=10
WORKER_MAX_ATTEMPTS=5
WORKER_RETRY_BASE_SECONDS=2
```

La queue et la DLQ sont stockées dans PostgreSQL. Les tables sont créées automatiquement au démarrage de l'API ou du worker.

## Jira

Le service utilise REST API v3. Une issue existante est mise à jour lorsque l'idempotency record contient son `jira_issue_key`. Les appels disposent de trois tentatives avec backoff `1s/2s`.

## Elasticsearch

```dotenv
ELASTICSEARCH_ENABLED=true
ELASTICSEARCH_URL=https://elasticsearch.example.com:443
ELASTICSEARCH_API_KEY=<secret>
ELASTICSEARCH_INDEX_PREFIX=gitlab-pipelines
```

Les index sont quotidiens : `gitlab-pipelines-YYYY.MM.DD`.

## OpenTelemetry

```dotenv
OTEL_ENABLED=true
OTEL_SERVICE_NAME=gitlab-jira-manual-hook
OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317
OTEL_INSECURE=true
```

Les traces FastAPI et HTTPX ainsi que les compteurs applicatifs sont exportés via OTLP.

## Policy

La policy est **deny-by-default** :

```yaml
projects:
  "12345":
    enabled: true
    stages: [deploy, production]
    jobs: [deploy_production, rollback_production]
    jira_project_key: OPS
    jira_issue_type: Task
```

Un projet absent ou sans `enabled: true` est refusé.

## Secrets

Ne jamais versionner `.env`, tokens GitLab/Jira, API keys Elasticsearch, mots de passe PostgreSQL ou secrets Kubernetes réels.
