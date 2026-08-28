# Guide d'utilisation

## 1. Prérequis

- Python 3.12+ pour le développement
- PostgreSQL pour l'idempotence
- Un projet Jira avec accès à l'API REST v3
- Un GitLab permettant de configurer des Project ou Group Webhooks
- Elasticsearch 8/9 compatible avec le client utilisé, si l'observabilité est activée
- Kibana pour l'exploitation des données

## 2. Démarrage local

```bash
cp .env.example .env
make compose-up
make test
```

Vérifier le service :

```bash
curl http://localhost:8000/health
curl http://localhost:8000/ready
```

## 3. Configurer le webhook Job

Dans GitLab, ajouter un webhook vers :

```text
https://<host>/webhook/gitlab
```

Activer **Job events** et utiliser `WEBHOOK_SECRET` comme secret token.

Le service ne crée un ticket que si :

- l'événement est un Job Hook ;
- le job est en `manual` ;
- le projet est explicitement activé ;
- le stage et le job satisfont la policy ;
- l'action n'a pas déjà été traitée.

## 4. Configurer le webhook Pipeline

Ajouter un second webhook :

```text
https://<host>/webhook/gitlab/pipeline
```

Activer **Pipeline events** avec le même secret.

Les événements pipeline sont envoyés vers Elasticsearch lorsque `ELASTICSEARCH_ENABLED=true`.

## 5. Cycle GitLab → Jira

```text
manual Job
   ↓
Webhook
   ↓
Authentication
   ↓
Policy
   ↓
Idempotency
   ↓
Jira REST API
   ↓
JIRA-123
```

En cas d'échec Jira, l'action est marquée `failed` et le webhook renvoie une réponse non-success afin de permettre un retry côté GitLab.

## 6. Cycle GitLab → Elasticsearch

```text
Pipeline Hook
   ↓
Authentication
   ↓
Pipeline normalization
   ↓
Elasticsearch
   ↓
gitlab-pipelines-YYYY.MM.DD
   ↓
Kibana
```

Une erreur Elasticsearch est volontairement non bloquante pour le traitement GitLab → Jira.

## 7. Production

### Docker Compose

```bash
docker compose -f deploy/docker-compose.prod.yml up -d
```

### Kubernetes

Appliquer les manifests dans l'ordre : namespace, configuration, secrets, deployment, service puis ingress. Les fichiers `*.example.yaml` doivent être personnalisés avant utilisation.

## 8. Vérification

Après configuration, tester successivement :

1. un pipeline normal ;
2. un job `manual` autorisé ;
3. un job `manual` non autorisé ;
4. une nouvelle livraison du même webhook ;
5. un pipeline `failed` ;
6. une panne temporaire d'Elasticsearch.

Le second envoi du même job ne doit pas créer un second ticket Jira.
