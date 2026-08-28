from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from app.services.webhook_service import ManualJob


class PolicyService:
    """Evaluate whether a manual GitLab job is allowed to create a Jira issue.

    Policy is deliberately fail-closed: a missing or invalid policy file, or a
    project that is not explicitly enabled, is rejected.
    """

    def __init__(self, path: str):
        self.path = Path(path)
        self.data: dict[str, Any] = {}
        if not self.path.exists():
            return

        loaded = yaml.safe_load(self.path.read_text(encoding="utf-8"))
        if isinstance(loaded, dict):
            self.data = loaded

    def allowed(self, job: ManualJob) -> bool:
        if not self.data:
            return False

        defaults = self.data.get("defaults") or {}
        projects = self.data.get("projects") or {}
        if not isinstance(projects, dict):
            return False

        key = str(job.project_id)
        project = projects.get(key) or projects.get(job.project_name)
        if project is None:
            project = defaults
        if not isinstance(project, dict):
            return False

        # Explicit opt-in is required. Never default to enabled.
        if project.get("enabled", False) is not True:
            return False

        stages = project.get("stages") or []
        jobs = project.get("jobs") or []
        if not isinstance(stages, list) or not isinstance(jobs, list):
            return False

        if stages and job.stage not in stages:
            return False
        if jobs and job.job_name not in jobs:
            return False

        return True
