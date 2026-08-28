# Queue, Worker et Dead-Letter

## Principe

Lorsque `QUEUE_ENABLED=true`, le webhook valide la policy, enregistre l'idempotence puis dépose le payload dans PostgreSQL. L'API retourne `202 Accepted` sans attendre Jira.

```text
GitLab → API → policy → manual_actions → webhook_queue → Worker → Jira
                                      │                    │
                                      └──────── retry ─────┘
                                                           ↓
                                                          DLQ
```

## Migrations Alembic

Le schéma durable de queue/DLQ est géré par Alembic et non plus créé dynamiquement par l'application.

```bash
alembic upgrade head
```

Créer une nouvelle migration :

```bash
alembic revision -m "describe change"
```

Les migrations sont versionnées dans `alembic/versions/`. En production, exécuter `alembic upgrade head` comme étape contrôlée du déploiement, avant le rollout des replicas API/worker.

## Tables

- `webhook_queue` : messages en attente/en cours.
- `webhook_dead_letters` : messages ayant épuisé leurs tentatives.
- `manual_actions` : idempotence et état de la synchronisation Jira.

## Worker

```bash
gitlab-jira-worker
# ou
python -m app.worker
```

Variables :

```text
WORKER_POLL_INTERVAL=2
WORKER_BATCH_SIZE=10
WORKER_MAX_ATTEMPTS=5
WORKER_RETRY_BASE_SECONDS=2
```

Le délai est `base * 2^attempt`.

## Concurrence et reprise

Les workers utilisent `FOR UPDATE SKIP LOCKED`. Un verrou de plus de dix minutes peut être repris afin d'éviter les messages bloqués après un crash.

## Dead-letter

Après `WORKER_MAX_ATTEMPTS`, le message est déplacé dans `webhook_dead_letters` avec son payload et l'erreur. Il peut être réinjecté :

```bash
python scripts/requeue-dlq.py <dead-letter-uuid>
```

Le compteur de tentatives est réinitialisé.

## Jira

Avant création, le worker recherche `jira_issue_key`. S'il existe, l'issue est mise à jour ; sinon elle est créée. Cela limite le risque de doublons après reprise d'un traitement.

## Kubernetes / PostgreSQL

Le worker est séparé de l'API :

```text
deploy/kubernetes/worker-deployment.yaml
deploy/docker-compose.prod.yml
```

PostgreSQL est isolé dans un StatefulSet avec `volumeClaimTemplates` :

```text
postgres-0
   └── postgres-data-postgres-0 (10Gi)
```

Le PVC reste associé au Pod ordinal et fournit un stockage persistant lors des recréations du Pod.
