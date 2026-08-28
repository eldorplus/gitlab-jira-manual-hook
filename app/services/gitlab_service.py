from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class GitLabService:
    """Small GitLab API client configuration holder for future job actions."""

    base_url: str
    token: str | None = None

    def job_play_url(self, project_id: int, job_id: int) -> str:
        return f"{self.base_url.rstrip('/')}/api/v4/projects/{project_id}/jobs/{job_id}/play"

    @staticmethod
    def extract_job_links(payload: dict[str, Any]) -> tuple[str, str]:
        project = payload.get("project") or {}
        pipeline = payload.get("pipeline") or {}
        build = payload.get("build") or {}
        project_url = str(project.get("web_url") or "")
        job_url = str(build.get("build_url") or build.get("web_url") or "")
        if not job_url and project_url and build.get("id"):
            job_url = f"{project_url}/-/jobs/{build['id']}"
        pipeline_url = str(pipeline.get("web_url") or "")
        return job_url, pipeline_url
