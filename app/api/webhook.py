import hmac
import logging
from fastapi import APIRouter, Header, HTTPException, Request, Response

from app.config import get_settings
from app.repositories.manual_action_repository import ManualActionRepository
from app.services.elastic_service import ElasticService
from app.services.jira_service import JiraService
from app.services.policy_service import PolicyService
from app.services.webhook_service import parse_gitlab_job

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/webhook/gitlab", status_code=204)
async def gitlab_webhook(request: Request, x_gitlab_token: str | None = Header(default=None)) -> Response:
    settings = get_settings()
    if not x_gitlab_token or not hmac.compare_digest(x_gitlab_token, settings.webhook_secret):
        raise HTTPException(status_code=401, detail="Invalid GitLab webhook token")
    try:
        payload = await request.json()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid JSON payload") from exc

    job = parse_gitlab_job(payload)
    if job is None:
        return Response(status_code=204)

    # Elasticsearch is best-effort: observability must never block GitLab.
    if settings.elasticsearch_enabled and settings.elasticsearch_url:
        elastic = ElasticService(
            settings.elasticsearch_url,
            settings.elasticsearch_index_prefix,
            settings.elasticsearch_api_key or None,
        )
        await elastic.publish_job(job, event="manual")
        await elastic.close()

    if not PolicyService(settings.project_config).allowed(job):
        return Response(status_code=204)

    repo = ManualActionRepository(settings.database_url)
    inserted, existing_key = await repo.record_or_get(job)
    if not inserted:
        logger.info("manual job already processed", extra={"job_id": job.job_id, "jira_issue_key": existing_key})
        return Response(status_code=204)

    try:
        issue_key = await JiraService(settings).create_issue(job)
        await repo.set_created(job, issue_key)
    except Exception:
        await repo.set_failed(job)
        logger.exception("failed to create Jira issue", extra={"job_id": job.job_id})
        raise HTTPException(status_code=502, detail="Jira issue creation failed")
    return Response(status_code=204)
