from __future__ import annotations

from pathlib import Path
from typing import Any
import yaml

from app.services.webhook_service import ManualJob


class PolicyService:
    def __init__(self, path: str):
        self.path = Path(path)
        self.data: dict[str, Any] = {}
        if self.path.exists():
            self.data = yaml.safe_load(self.path.read_text()) or {}

    def allowed(self, job: ManualJob) -> bool:
        defaults = self.data.get("defaults", {})
        key = str(job.project_id)
        project = (self.data.get("projects") or {}).get(key) or (self.data.get("projects") or {}).get(job.project_name) or defaults
        if not project.get("enabled", True):
            return False
        stages = project.get("stages") or []
        jobs = project.get("jobs") or []
        if stages and job.stage not in stages:
            return False
        if jobs and job.job_name not in jobs:
            return False
        return True
