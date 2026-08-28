# Configuration

## Variables d'environnement

| Variable | Obligatoire | Description |
|---|---:|---|
| `WEBHOOK_SECRET` | Oui | Secret utilisé par GitLab Webhooks |
| `DATABASE_URL` | Oui | URL PostgreSQL |
| `JIRA_BASE_URL` | Oui | URL du site Jira |
| `JIRA_EMAIL` | Oui | Compte API Jira |
| `JIRA_API_TOKEN` | Oui | Token API Jira |
| `JIRA_PROJECT_KEY` | Oui | Projet Jira cible par défaut |
| `JIRA_ISSUE_TYPE` | Oui | Type d'issue Jira |
| `PROJECT_CONFIG` | Non | Chemin vers la policy YAML |
| `ELASTICSEARCH_ENABLED` | Non | Active la publication Elasticsearch, défaut `false` |
| `ELASTICSEARCH_URL` | Si activé | URL Elasticsearch |
| `ELASTICSEARCH_API_KEY` | Recommandé | API key Elasticsearch |
| `ELASTICSEARCH_INDEX_PREFIX` | Non | Préfixe des index, défaut `gitlab-pipelines` |
| `LOG_LEVEL` | Non | Niveau de log, défaut `INFO` |

## Exemple Elasticsearch

```dotenv
ELASTICSEARCH_ENABLED=true
ELASTICSEARCH_URL=https://elasticsearch.example.com:443
ELASTICSEARCH_API_KEY=<secret>
ELASTICSEARCH_INDEX_PREFIX=gitlab-pipelines
```

## Policy

La policy est **deny-by-default**. Un projet doit être explicitement activé :

```yaml
projects:
  "12345":
    enabled: true
    stages:
      - deploy
      - production
    jobs:
      - deploy_production
      - rollback_production
    jira_project_key: OPS
    jira_issue_type: Task
```

Un projet absent ou sans `enabled: true` est refusé.

`stages` et `jobs` peuvent être utilisés pour restreindre les jobs autorisés. Une liste non vide impose une correspondance exacte.

## Secrets

Ne jamais versionner :

- `.env`
- token GitLab
- token Jira
- API key Elasticsearch
- mots de passe PostgreSQL

En Kubernetes, utiliser les Secrets fournis comme exemples et les remplacer par de vraies valeurs via un gestionnaire de secrets adapté.

## Index Elasticsearch

Le préfixe par défaut produit :

```text
gitlab-pipelines-2026.08.28
gitlab-pipelines-2026.08.29
```

Cette stratégie facilite la rétention, les Data Views Kibana et les opérations d'archivage.
