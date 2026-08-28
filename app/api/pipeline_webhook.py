import hmac

from fastapi import APIRouter, Header, HTTPException, Request, Response

from app.config import get_settings
from app.services.elastic_service import ElasticService
from app.services.pipeline_observability_service import PipelineObservabilityService

router = APIRouter()


@router.post("/webhook/gitlab/pipeline", status_code=204)
async def gitlab_pipeline_webhook(request: Request, x_gitlab_token: str | None = Header(default=None)) -> Response:
    settings = get_settings()
    if not x_gitlab_token or not hmac.compare_digest(x_gitlab_token, settings.webhook_secret):
        raise HTTPException(status_code=401, detail="Invalid GitLab webhook token")

    try:
        payload = await request.json()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid JSON payload") from exc

    if payload.get("object_kind") != "pipeline":
        return Response(status_code=204)
    if not settings.elasticsearch_enabled or not settings.elasticsearch_url:
        return Response(status_code=204)

    elastic = ElasticService(
        settings.elasticsearch_url,
        settings.elasticsearch_index_prefix,
        settings.elasticsearch_api_key or None,
    )
    try:
        await PipelineObservabilityService(elastic).publish(payload, elastic)
    finally:
        await elastic.close()
    return Response(status_code=204)
