# Guide d'utilisation

## 1. Prérequis

- Python 3.12+ pour le développement
- PostgreSQL 17+ en production
- Jira avec accès REST API v3
- GitLab avec Project/Group Webhooks
- Elasticsearch et Kibana si l'observabilité est activée
- OTLP Collector si les traces/métriques OpenTelemetry sont activées

## 2. Démarrage local

```bash
cp .env.example .env
make compose-up
make test
```

Démarrer le worker dans un second terminal :

```bash
python -m app.worker
```

Vérifier :

```bash
curl http://localhost:8000/health
curl http://localhost:8000/ready
```

## 3. Webhook Job

Configurer dans GitLab :

```text
https://<host>/webhook/gitlab
```

Activer **Job events** et utiliser `WEBHOOK_SECRET` comme secret token.

Pour un job `manual` autorisé :

```text
GitLab → API → Policy → Idempotency → Queue → Worker → Jira
```

Le webhook retourne `202 Accepted` après mise en queue lorsque `QUEUE_ENABLED=true`. L'API ne bloque donc pas sur Jira.

## 4. Webhook Pipeline

Configurer :

```text
https://<host>/webhook/gitlab/pipeline
```

Activer **Pipeline events**.

Les données sont normalisées et envoyées vers Elasticsearch lorsque `ELASTICSEARCH_ENABLED=true`.

## 5. Worker et retries

```bash
gitlab-jira-worker
```

Le worker consomme `webhook_queue`. Les erreurs sont retentées avec backoff exponentiel. Après `WORKER_MAX_ATTEMPTS`, le message est déplacé vers `webhook_dead_letters`.

Un message DLQ peut être réinjecté via `DeadLetterService` après correction de la cause.

## 6. Synchronisation Jira

Si une action possède déjà un `jira_issue_key`, le worker met à jour l'issue existante au lieu d'en créer une nouvelle. Les champs GitLab sont synchronisés et les appels REST sont instrumentés et retentés.

## 7. OpenTelemetry

Activer :

```dotenv
OTEL_ENABLED=true
OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317
```

Le service exporte des traces FastAPI/HTTPX et des métriques applicatives vers l'OTLP Collector.

## 8. Kibana

Importer les assets :

```bash
cd deploy/kibana
KIBANA_URL=https://kibana.example.com KIBANA_API_KEY=... ./import.sh
```

Data View : `gitlab-pipelines-*` ; champ temporel : `@timestamp`.

## 9. Kubernetes

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

## 10. Vérification

Tester :

1. pipeline normal ;
2. job `manual` autorisé ;
3. job `manual` refusé par policy ;
4. doublon du même webhook ;
5. succès Jira ;
6. échec Jira puis retry ;
7. dépassement du nombre maximal de retries → DLQ ;
8. pipeline `failed` dans Kibana ;
9. traces et métriques dans le backend OTLP ;
10. redémarrage du worker avec messages persistés.
