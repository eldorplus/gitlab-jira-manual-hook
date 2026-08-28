from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from app.services.elastic_service import ElasticService

logger = logging.getLogger(__name__)


class PipelineObservabilityService:
    """Normalize GitLab pipeline webhook events for Elasticsearch/Kibana."""

    def __init__(self, elastic: ElasticService):
        self.elastic = elastic

    async def publish(self, payload: dict[str, Any]) -> None:
        attributes = payload.get("object_attributes") or {}
        project = payload.get("project") or {}
        user = payload.get("user") or {}
        pipeline_id = attributes.get("id")
        if pipeline_id is None:
            return

        document = {
            "@timestamp": datetime.now(timezone.utc),
            "event": {
                "kind": "event",
                "category": "ci",
                "type": ["pipeline"],
                "action": "pipeline_status",
            },
            "gitlab": {
                "project": {
                    "id": project.get("id"),
                    "name": project.get("name"),
                    "path_with_namespace": project.get("path_with_namespace"),
                    "url": project.get("web_url"),
                },
                "pipeline": {
                    "id": pipeline_id,
                    "status": attributes.get("status"),
                    "ref": attributes.get("ref"),
                    "sha": attributes.get("sha"),
                    "source": attributes.get("source"),
                    "url": attributes.get("url") or attributes.get("web_url"),
                },
                "user": {"id": user.get("id"), "username": user.get("username")},
            },
        }
        await self.elastic.publish_document(document)
