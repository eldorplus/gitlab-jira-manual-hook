from __future__ import annotations

import asyncio
import httpx

from app.config import Settings
from app.services.webhook_service import ManualJob


class JiraService:
    def __init__(self, settings: Settings):
        self.settings = settings

    async def create_issue(self, job: ManualJob) -> str:
        if not self.settings.jira_base_url or not self.settings.jira_email or not self.settings.jira_api_token:
            raise RuntimeError("Jira configuration is incomplete")
        description = f"GitLab CI job waiting for manual action.\n\nProject: {job.project_name}\nPipeline: #{job.pipeline_id}\nJob: {job.job_name}\nStage: {job.stage}\nRef: {job.ref}\nCommit: {job.commit_sha}\nJob URL: {job.job_url}\nPipeline URL: {job.pipeline_url}"
        payload = {"fields": {
            "project": {"key": self.settings.jira_project_key},
            "issuetype": {"name": self.settings.jira_issue_type},
            "summary": f"[GitLab] Manual action required: {job.job_name}",
            "description": {"type": "doc", "version": 1, "content": [{"type": "paragraph", "content": [{"type": "text", "text": description}]}]},
            "labels": ["gitlab", "manual-action", job.stage.replace("_", "-")],
        }}
        url = f"{self.settings.jira_base_url.rstrip('/')}/rest/api/3/issue"
        last_error: Exception | None = None
        for attempt in range(3):
            try:
                async with httpx.AsyncClient(timeout=15) as client:
                    response = await client.post(url, auth=(self.settings.jira_email, self.settings.jira_api_token), json=payload, headers={"Accept": "application/json"})
                response.raise_for_status()
                return str(response.json()["key"])
            except (httpx.HTTPError, KeyError) as exc:
                last_error = exc
                if attempt < 2:
                    await asyncio.sleep(2 ** attempt)
        raise RuntimeError("Jira issue creation failed") from last_error
