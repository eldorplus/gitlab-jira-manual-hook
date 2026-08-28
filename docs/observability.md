# Observabilité GitLab CI → Elasticsearch / Kibana / OpenTelemetry

## Vue d'ensemble

```text
GitLab Pipeline Hook → FastAPI → Elasticsearch → Kibana
                           │
                           └→ OpenTelemetry → OTLP Collector → backend observability
```

## Elasticsearch

Endpoint : `POST /webhook/gitlab/pipeline`.

Index : `gitlab-pipelines-YYYY.MM.DD`.

Data View : `gitlab-pipelines-*` avec `@timestamp`.

Le document contient notamment `event.*`, `gitlab.project.*`, `gitlab.pipeline.*` et `gitlab.user.*`. Les timings, statut, source, SHA et failure reason sont conservés. Les données `jobs`, `stages`, `environment` et `runner` sont conservées lorsqu'elles sont présentes dans le webhook.

## Kibana automatisé

Les assets versionnés sont dans :

```text
deploy/kibana/data-view.json
deploy/kibana/gitlab-pipelines.ndjson
deploy/kibana/import.sh
```

Importer :

```bash
cd deploy/kibana
KIBANA_URL=https://kibana.example.com KIBANA_API_KEY=... ./import.sh
```

L'import utilise l'API Saved Objects de Kibana et `overwrite=true`, ce qui permet de rejouer le déploiement.

Le dashboard de base `GitLab CI Overview` est fourni comme point de départ. Les visualisations métier peuvent être versionnées dans le même NDJSON.

## Dashboards recommandés

### Pipeline overview

- volume de pipelines
- succès/échecs/cancellations
- taux de succès
- durée moyenne/P95/P99
- pipelines par projet, branche et source

### Pipeline failures

- `event.reason`
- `gitlab.pipeline.failure_reason`
- top projets/branches en échec
- durée des pipelines échoués

### Queue / Jira

Surveiller côté application :

- nombre d'éléments en attente
- retries
- DLQ
- créations Jira
- mises à jour Jira
- erreurs Jira

## OpenTelemetry

Configuration :

```dotenv
OTEL_ENABLED=true
OTEL_SERVICE_NAME=gitlab-jira-manual-hook
OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317
OTEL_INSECURE=true
```

### Traces

FastAPI et les appels HTTPX sont instrumentés. Les opérations Jira et queue disposent également de spans applicatifs.

Les attributs sensibles tels que tokens, mots de passe et contenu d'authentification ne doivent jamais être ajoutés aux spans.

### Métriques

Compteurs applicatifs prévus :

```text
gitlab_webhook_requests_total
gitlab_queue_events_total
jira_operations_total
```

Labels : statut de requête, action de queue, opération/résultat Jira.

## Queue et DLQ

La queue est persistante dans PostgreSQL :

```text
webhook_queue
webhook_dead_letters
```

Les workers utilisent `FOR UPDATE SKIP LOCKED`, avec retries exponentiels et récupération des verrous expirés.

## Corrélation

Utiliser :

```text
gitlab.project.id
gitlab.pipeline.id
gitlab.pipeline.sha
gitlab.pipeline.ref
```

et, pour les jobs manuels :

```text
gitlab.job.id
gitlab.job.name
gitlab.job.stage
```

## Résilience

Une panne Elasticsearch ne bloque pas les traitements métier. Une panne Jira est absorbée par la queue, puis retryée avant passage en DLQ.

## Rétention

Les index quotidiens facilitent l'application d'une ILM adaptée à l'environnement. La durée de rétention reste une décision d'exploitation.
