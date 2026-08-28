import pytest
from httpx import ASGITransport, AsyncClient

from app.config import get_settings
from app.main import create_app
from app.services.webhook_service import parse_gitlab_job


def payload(status="manual"):
    return {"object_kind": "build", "build_status": status, "project_id": 42, "project_name": "demo", "project": {"web_url": "https://gitlab.example/demo"}, "pipeline_id": 100, "build_id": 200, "build_name": "deploy_production", "build_stage": "deploy", "ref": "main", "commit": {"id": "abc123"}, "build_url": "https://gitlab.example/demo/-/jobs/200", "pipeline": {"url": "https://gitlab.example/demo/-/pipelines/100"}}


def test_parser_accepts_manual_job():
    job = parse_gitlab_job(payload())
    assert job is not None
    assert job.job_id == 200
    assert job.stage == "deploy"


def test_parser_rejects_non_manual_job():
    assert parse_gitlab_job(payload("success")) is None

@pytest.mark.asyncio
async def test_invalid_token():
    settings = get_settings()
    settings.webhook_secret = "secret"
    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/webhook/gitlab", headers={"X-Gitlab-Token": "wrong"}, json=payload())
    assert response.status_code == 401
