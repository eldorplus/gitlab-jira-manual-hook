import httpx
import pytest
import respx

from app.config import Settings
from app.services.jira_service import JiraService
from app.services.webhook_service import ManualJob


@pytest.mark.asyncio
@respx.mock
async def test_create_issue():
    route = respx.post("https://jira.example/rest/api/3/issue").mock(return_value=httpx.Response(201, json={"key": "OPS-123"}))
    settings = Settings(jira_base_url="https://jira.example", jira_email="bot@example.com", jira_api_token="token")
    job = ManualJob(1, "demo", "", 2, 3, "deploy", "deploy", "manual", "main", "abc", "", "")
    assert await JiraService(settings).create_issue(job) == "OPS-123"
    assert route.called
