from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from elasticsearch import AsyncElasticsearch

from app.services.webhook_service import ManualJob

logger = logging.getLogger(__name__)


class ElasticService:
    """Publish GitLab pipeline/job lifecycle events to Elasticsearch."""

    def __init__(self, url: str, index_prefix: str = "gitlab-pipelines", api_key: str | None = None):
        self.url = url.rstrip("/")
        self.index_prefix = index_prefix
        self.client = AsyncElasticsearch(self.url, api_key=api_key) if api_key else AsyncElasticsearch(self.url)

    def _index(self, timestamp: datetime | None = None) -> str:
        ts = timestamp or datetime.now(timezone.utc)
        return f"{self.index_prefix}-{ts:%Y.%m.%d}"

    async def publish_job(self, job: ManualJob, event: str = "job") -> None:
        document: dict[str, Any] = {
            "@timestamp": datetime.now(timezone.utc),
            "event": {"kind": "event", "category": "ci", "action": event},
            "gitlab": {
                "project": {
                    "id": job.project_id,
                    "name": job.project_name,
                    "url": job.project_web_url,
                },
                "pipeline": {"id": job.pipeline_id, "url": job.pipeline_url},
                "job": {
                    "id": job.job_id,
                    "name": job.job_name,
                    "stage": job.stage,
                    "status": job.status,
                    "url": job.job_url,
                },
                "ref": job.ref,
                "commit": {"sha": job.commit_sha},
            },
        }
        try:
            await self.client.index(index=self._index(), document=document)
        except Exception:
            # Observability must not make GitLab webhook processing fail.
            logger.exception("failed to publish GitLab event to Elasticsearch", extra={"job_id": job.job_id})

    async def close(self) -> None:
        await self.client.close()
