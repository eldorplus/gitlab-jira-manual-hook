# Synchronisation Jira

## Création

Un job GitLab `manual` autorisé produit une entrée `manual_actions` puis un message `jira.manual_job`.

Le worker crée une issue Jira avec :

- projet et type configurés ;
- résumé contenant le job ;
- description ADF avec projet, pipeline, job, stage, ref, commit et URLs ;
- labels `gitlab`, `manual-action` et stage.

## Mise à jour

Si `manual_actions.jira_issue_key` existe déjà, le worker met à jour l'issue au lieu de créer une seconde issue.

Cette logique est particulièrement importante après un retry ou un redémarrage du worker.

## Retry Jira

Chaque appel REST Jira dispose de trois tentatives avec backoff exponentiel. Les erreurs persistantes sont remontées au worker, qui applique ensuite le retry de queue puis la DLQ.

## Commentaires

`JiraService.add_comment()` est disponible pour enrichir ultérieurement les transitions de cycle de vie (pipeline terminé, déploiement réussi/échoué, rollback, etc.).

## Observabilité

Les opérations `create` et `update` sont instrumentées avec OpenTelemetry et les métriques :

```text
jira_operations_total{operation="create|update",result="success|failure"}
```

Les tokens Jira ne sont jamais ajoutés aux logs ou attributs de traces.
