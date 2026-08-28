from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class ActionRepository(Protocol):
    async def exists(self, project_id: int, pipeline_id: int, job_id: int) -> bool: ...


@dataclass(frozen=True)
class IdempotencyService:
    repository: ActionRepository

    async def already_processed(self, project_id: int, pipeline_id: int, job_id: int) -> bool:
        """Return True when this exact GitLab job has already been recorded."""
        return await self.repository.exists(project_id, pipeline_id, job_id)

    @staticmethod
    def key(project_id: int, pipeline_id: int, job_id: int) -> str:
        return f"gitlab:{project_id}:pipeline:{pipeline_id}:job:{job_id}"
