from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.services.elastic_service import ElasticService


class PipelineObservabilityService:
    """Normalize GitLab pipeline webhook events for Elasticsearch/Kibana."""

    @staticmethod
    def _parse_time(value: Any) -> datetime | None:
        if not value or not isinstance(value, str):
            return None
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None

    async def publish(self, payload: dict[str, Any], elastic: ElasticService) -> None:
        attributes = payload.get("object_attributes") or {}
        project = payload.get("project") or {}
        user = payload.get("user") or {}
        pipeline_id = attributes.get("id")
        if pipeline_id is None:
            return

        created = self._parse_time(attributes.get("created_at"))
        updated = self._parse_time(attributes.get("updated_at"))
        finished = self._parse_time(attributes.get("finished_at"))
        started = self._parse_time(attributes.get("started_at"))
        duration = attributes.get("duration")
        if duration is None and started and finished:
            duration = (finished - started).total_seconds()

        document = {
            "@timestamp": finished or updated or started or created or datetime.now(timezone.utc),
            "event": {
                "kind": "event", "category": "ci", "type": ["pipeline"],
                "action": "pipeline_status", "outcome": attributes.get("status"),
                "reason": attributes.get("failure_reason"),
            },
            "gitlab": {
                "project": {
                    "id": project.get("id"), "name": project.get("name"),
                    "path_with_namespace": project.get("path_with_namespace"), "url": project.get("web_url"),
                },
                "pipeline": {
                    "id": pipeline_id, "status": attributes.get("status"),
                    "ref": attributes.get("ref"), "sha": attributes.get("sha"),
                    "source": attributes.get("source"), "url": attributes.get("url") or attributes.get("web_url"),
                    "duration_seconds": duration,
                    "queued_duration_seconds": attributes.get("queued_duration"),
                    "created_at": created, "started_at": started, "finished_at": finished,
                    "failure_reason": attributes.get("failure_reason"),
                },
                "user": {"id": user.get("id"), "username": user.get("username")},
            },
        }
        for source, target in (("jobs", "jobs"), ("builds", "jobs"), ("stages", "stages"), ("environment", "environment"), ("runner", "runner")):
            if payload.get(source) is not None:
                document["gitlab"][target] = payload[source]

        await elastic.publish_document(document, document["@timestamp"])
