from contextlib import asynccontextmanager

from fastapi import FastAPI
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

from app.api.pipeline_webhook import router as pipeline_router
from app.api.webhook import router as job_router
from app.config import get_settings
from app.services.telemetry import configure_telemetry


def create_app() -> FastAPI:
    settings = get_settings()
    configure_telemetry(settings)
    app = FastAPI(title=settings.app_name, version="0.2.0")
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
