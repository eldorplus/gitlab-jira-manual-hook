from contextlib import asynccontextmanager

from fastapi import FastAPI
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

from app.api.pipeline_webhook import router as pipeline_router
from app.api.webhook import router as job_router
from app.config import get_settings
from app.repositories.queue_repository import QueueRepository
from app.services.telemetry import configure_telemetry


def create_app() -> FastAPI:
    settings = get_settings()
    configure_telemetry(settings)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        if settings.queue_enabled:
            await QueueRepository(settings.database_url).ensure_schema()
        yield

    app = FastAPI(title=settings.app_name, version="0.2.0", lifespan=lifespan)
    app.include_router(job_router)
    app.include_router(pipeline_router)
    if settings.otel_enabled:
        FastAPIInstrumentor.instrument_app(app)
        HTTPXClientInstrumentor().instrument()

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/ready")
    async def ready() -> dict[str, str]:
        return {"status": "ready"}

    return app


app = create_app()
