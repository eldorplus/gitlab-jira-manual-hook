import httpx

from app.config import Settings
from app.services.webhook_service import ManualJob


class JiraService:
    def __init__(self, settings: Settings):
        self.settings = settings

    async def create_issue(self, job: ManualJob) -> str:
        if not self.settings.jira_base_url or not self.settings.jira_email or not self.settings.jira_api_token:
            raise RuntimeError("Jira is not configured")

        summary = f"[GitLab] Manual action required: {job.job_name}"
        description = (
            "A GitLab CI job is waiting for manual action.\n\n"
            f"Project: {job.project_name}\n"
            f"Pipeline: #{job.pipeline_id}\n"
            f"Job: {job.job_name}\n"
            f"Stage: {job.stage}\n"
            f"Ref: {job.ref}\n"
            f"Commit: {job.commit_sha}\n"
            f"GitLab job: {job.job_url}\n"
            f"Pipeline: {job.pipeline_url}"
        )
        fields = {
            "project": {"key": self.settings.jira_project_key},
            "issuetype": {"name": self.settings.jira_issue_type},
            "summary": summary,
            "description": {
                "type": "doc", "version": 1,
                "content": [{"type": "paragraph", "content": [{"type": "text", "text": description}]}],
            },
            "labels": ["gitlab", "manual-action"],
        }
        url = f"{self.settings.jira_base_url.rstrip('/')}/rest/api/3/issue"
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(url, auth=(self.settings.jira_email, self.settings.jira_api_token), json={"fields": fields})
            response.raise_for_status()
            return response.json()["key"]
