# Observabilité GitLab CI → Elasticsearch / Kibana

## Objectif

Le service collecte les événements GitLab Pipeline afin de suivre l'état, les performances et les causes d'échec des pipelines dans Kibana.

## Endpoint

```text
POST /webhook/gitlab/pipeline
```

Dans GitLab, sélectionner **Pipeline events**.

## Index

Les documents sont écrits dans :

```text
gitlab-pipelines-YYYY.MM.DD
```

Data View Kibana recommandé :

```text
gitlab-pipelines-*
```

Champ temporel : `@timestamp`.

## Schéma principal

### ECS

```text
event.kind
event.category
event.type
event.action
event.outcome
event.reason
@timestamp
```

### GitLab project

```text
gitlab.project.id
gitlab.project.name
gitlab.project.path_with_namespace
gitlab.project.url
```

### Pipeline

```text
gitlab.pipeline.id
gitlab.pipeline.status
gitlab.pipeline.ref
gitlab.pipeline.sha
gitlab.pipeline.source
gitlab.pipeline.url
gitlab.pipeline.duration_seconds
gitlab.pipeline.queued_duration_seconds
gitlab.pipeline.created_at
gitlab.pipeline.started_at
gitlab.pipeline.finished_at
gitlab.pipeline.failure_reason
```

### User

```text
gitlab.user.id
gitlab.user.username
```

Lorsque GitLab les fournit, les métadonnées suivantes sont également conservées :

```text
gitlab.jobs
gitlab.stages
gitlab.environment
gitlab.runner
```

## Dashboards Kibana recommandés

### 1. Pipeline overview

Visualisations :

- nombre de pipelines
- pipelines par statut
- taux de succès
- taux d'échec
- durée moyenne
- durée P95
- pipelines par projet
- pipelines par branche

Filtres utiles :

```text
gitlab.project.name
 gitlab.pipeline.ref
gitlab.pipeline.source
gitlab.pipeline.status
```

### 2. Pipeline failures

Afficher :

- échecs dans le temps
- top projets en échec
- top branches en échec
- `event.reason`
- `gitlab.pipeline.failure_reason`
- durée des pipelines échoués

### 3. Performance

Suivre :

- `gitlab.pipeline.duration_seconds`
- `gitlab.pipeline.queued_duration_seconds`
- moyenne
- médiane
- P95
- P99

Cela permet de distinguer un problème de pipeline d'un problème de disponibilité/capacité des runners.

### 4. Deployment / Environment

Lorsque les données sont disponibles :

- pipelines par environnement
- succès/échec par environnement
- durée des déploiements
- runner utilisé
- fréquence des déploiements

### 5. Manual actions

Les événements Job peuvent être corrélés avec les pipelines afin de suivre :

- jobs `manual`
- tickets Jira générés
- projets concernés
- stages concernés
- jobs nécessitant une validation humaine

## Corrélation

Les champs suivants peuvent servir de clés de corrélation :

```text
gitlab.project.id
gitlab.pipeline.id
gitlab.pipeline.sha
gitlab.pipeline.ref
```

Pour le parcours Job → Jira, utiliser également :

```text
gitlab.job.id
gitlab.job.name
gitlab.job.stage
```

## Résilience

La publication Elasticsearch est best-effort. Une panne du cluster Elasticsearch ne doit pas empêcher la création d'un ticket Jira pour un job manuel autorisé.

## Rétention

La rotation quotidienne des index permet d'appliquer ensuite une politique ILM adaptée aux besoins de conservation. Le projet ne fournit pas de politique ILM imposée afin de laisser la durée de rétention au contexte d'exploitation.

## Sécurité

Utiliser une API key Elasticsearch avec les droits minimaux nécessaires à l'indexation. Ne jamais placer cette clé dans le repository ou dans un document Elasticsearch.
