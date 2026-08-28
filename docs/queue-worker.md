# Queue, Worker et Dead-Letter

## Principe

Le webhook GitLab ne réalise plus l'appel Jira lorsque `QUEUE_ENABLED=true`. Il valide la policy, enregistre l'idempotence puis dépose le payload dans PostgreSQL.

```text
GitLab → API → policy → manual_actions → webhook_queue → Worker → Jira
                                      │
                                      └─ retry → DLQ
```

## Tables

`webhook_queue` contient les travaux en attente, leur nombre de tentatives, la date de disponibilité et le verrou de traitement.

`webhook_dead_letters` conserve les travaux définitivement échoués et leur dernière erreur.

Les tables sont créées automatiquement au démarrage lorsque la queue est activée.

## Worker

Commande :

```bash
gitlab-jira-worker
```

ou :

```bash
python -m app.worker
```

Variables :

```text
WORKER_POLL_INTERVAL=2
WORKER_BATCH_SIZE=10
WORKER_MAX_ATTEMPTS=5
WORKER_RETRY_BASE_SECONDS=2
```

Le délai de retry suit une progression exponentielle : `base * 2^attempt`.

## Concurrence

Les workers utilisent `FOR UPDATE SKIP LOCKED`. Plusieurs réplicas peuvent donc consommer la queue sans prendre le même élément. Un verrou vieux de dix minutes est récupérable pour éviter les messages bloqués après la disparition d'un worker.

## Dead-letter

Après le nombre maximal de tentatives, le message est déplacé vers `webhook_dead_letters`.

Le service `DeadLetterService` permet de remettre un message en queue avec un compteur de tentatives réinitialisé.

## Production

Kubernetes utilise un Deployment séparé :

```text
deploy/kubernetes/worker-deployment.yaml
```

Il peut être scalé indépendamment de l'API.

## Bonnes pratiques

- garder la queue sur PostgreSQL persistant ;
- surveiller la profondeur de queue et le nombre de DLQ ;
- conserver les erreurs sans secrets ;
- dimensionner les workers selon le débit Jira ;
- préférer plusieurs workers avec `SKIP LOCKED` plutôt qu'un worker unique.
