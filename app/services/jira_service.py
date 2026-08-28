from __future__ import annotations

import asyncio
import httpx

from app.config import Settings
from app.services.webhook_service import ManualJob


class JiraService:
    def __init__(self, settings: Settings):
        self.settings = settings

    def _fields(self, job: ManualJob) -> dict:
        description = f"GitLab CI job waiting for manual action.\n\nProject: {job.project_name}\nPipeline: #{job.pipeline_id}\nJob: {job.job_name}\nStage: {job.stage}\nRef: {job.ref}\nCommit: {job.commit_sha}\nJob URL: {job.job_url}\nPipeline URL: {job.pipeline_url}"
        return {
            "project": {"key": self.settings.jira_project_key},
            "issuetype": {"name": self.settings.jira_issue_type},
            "summary": f"[GitLab] Manual action required: {job.job_name}",
            "description": {"type": "doc", "version": 1, "content": [{"type": "paragraph", "content": [{"type": "text", "text": description}]}]},
            "labels": ["gitlab", "manual-action", job.stage.replace("_", "-")],
        }

    def _headers(self) -> dict[str, str]:
        return {"Accept": "application/json", "Content-Type": "application/json"}

    async def _request(self, method: str, url: str, **kwargs) -> httpx.Response:
        last_error: Exception | None = None
        for attempt in range(3):
            try:
                async with httpx.AsyncClient(timeout=15) as client:
                    response = await client.request(method, url, auth=(self.settings.jira_email, self.settings.jira_api_token), headers=self._headers(), **kwargs)
                response.raise_for_status()
                return response
            except httpx.HTTPError as exc:
                last_error = exc
                if attempt < 2:
                    await asyncio.sleep(2 ** attempt)
        raise RuntimeError("Jira API request failed") from last_error

    async def create_issue(self, job: ManualJob) -> str:
        if not self.settings.jira_base_url or not self.settings.jira_email or not self.settings.jira_api_token:
            raise RuntimeError("Jira configuration is incomplete")
        response = await self._request("POST", f"{self.settings.jira_base_url.rstrip('/')}/rest/api/3/issue", json={"fields": self._fields(job)})
        return str(response.json()["key"])

    async def update_issue(self, issue_key: str, job: ManualJob) -> None:
        await self._request("PUT", f"{self.settings.jira_base_url.rstrip('/')}/rest/api/3/issue/{issue_key}", json={"fields": self._fields(job)})

    async def add_comment(self, issue_key: str, text: str) -> None:
        body = {"body": {"type": "doc", "version": 1, "content": [{"type": "paragraph", "content": [{"type": "text", "text": text}]}]}}
        await self._request("POST", f"{self.settings.jira_base_url.rstrip('/')}/rest/api/3/issue/{issue_key}/comment", json=body)

    async def create_or_update_issue(self, job: ManualJob, existing_issue_key: str | None = None) -> str:
        if existing_issue_key:
            await self.update_issue(existing_issue_key, job)
            return existing_issue_key
        return await self.create_issue(job)
