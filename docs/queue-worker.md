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

## Tables

- `webhook_queue` : messages en attente/en cours.
- `webhook_dead_letters` : messages ayant épuisé leurs tentatives.
- `manual_actions` : idempotence et état de la synchronisation Jira.

Les tables de queue/DLQ sont créées automatiquement lorsque la queue est activée.

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

## Kubernetes / Docker

Le worker est séparé de l'API :

```text
deploy/kubernetes/worker-deployment.yaml
deploy/docker-compose.prod.yml
```

Il peut être scalé indépendamment de l'API.
