from fastapi import FastAPI

from app.api.pipeline_webhook import router as pipeline_router
from app.api.webhook import router as job_router
from app.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, version="0.1.0")
    app.include_router(job_router)
    app.include_router(pipeline_router)

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/ready")
    async def ready() -> dict[str, str]:
        return {"status": "ready"}

    return app


app = create_app()
