import pytest
import respx
from httpx import Response

from app.config import Settings
from app.services.jira_service import JiraService
from app.services.webhook_service import ManualJob


def job():
    return ManualJob(42, "demo", "https://gitlab.example/demo", 100, 200, "deploy_production", "deploy", "main", "abc123", "https://gitlab.example/demo/-/jobs/200", "https://gitlab.example/demo/-/pipelines/100")


@pytest.mark.asyncio
@respx.mock
async def test_update_existing_jira_issue():
    settings = Settings(jira_base_url="https://jira.example", jira_email="bot@example.com", jira_api_token="token")
    route = respx.put("https://jira.example/rest/api/3/issue/OPS-123").mock(return_value=Response(204))
    await JiraService(settings).create_or_update_issue(job(), "OPS-123")
    assert route.called
