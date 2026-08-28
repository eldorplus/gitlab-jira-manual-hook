import pytest
import respx
from httpx import Response

from app.config import Settings
from app.services.jira_service import JiraService
from app.services.webhook_service import ManualJob


def job():
    return ManualJob(
        project_id=42,
        project_name="demo",
        project_web_url="https://gitlab.example/demo",
        pipeline_id=100,
        job_id=200,
        job_name="deploy_production",
        stage="deploy",
        status="manual",
        ref="main",
        commit_sha="abc123",
        job_url="https://gitlab.example/demo/-/jobs/200",
        pipeline_url="https://gitlab.example/demo/-/pipelines/100",
    )


@pytest.mark.asyncio
@respx.mock
async def test_update_existing_jira_issue():
    settings = Settings(jira_base_url="https://jira.example", jira_email="bot@example.com", jira_api_token="token")
    route = respx.put("https://jira.example/rest/api/3/issue/OPS-123").mock(return_value=Response(204))
    await JiraService(settings).create_or_update_issue(job(), "OPS-123")
    assert route.called
