import hmac
from fastapi import APIRouter, Header, HTTPException, Request, Response

from app.config import get_settings
from app.services.jira_service import JiraService
from app.services.webhook_service import parse_gitlab_job

router = APIRouter()


@router.post("/webhook/gitlab", status_code=204)
async def gitlab_webhook(request: Request, x_gitlab_token: str | None = Header(default=None)) -> Response:
    settings = get_settings()
    if not x_gitlab_token or not hmac.compare_digest(x_gitlab_token, settings.webhook_secret):
        raise HTTPException(status_code=401, detail="Invalid GitLab webhook token")

    payload = await request.json()
    job = parse_gitlab_job(payload)
    if job is None:
        return Response(status_code=204)

    # V1: create Jira issue. Idempotency repository will be added in the next iteration.
    await JiraService(settings).create_issue(job)
    return Response(status_code=204)
