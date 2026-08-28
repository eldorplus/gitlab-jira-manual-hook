from __future__ import annotations

from contextlib import contextmanager

from opentelemetry import metrics, trace
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.metrics.export import ConsoleMetricExporter, PeriodicExportingMetricReader

from app.config import Settings


REQUEST_COUNTER = None
QUEUE_COUNTER = None
JIRA_COUNTER = None


def configure_telemetry(settings: Settings) -> None:
    global REQUEST_COUNTER, QUEUE_COUNTER, JIRA_COUNTER
    if not settings.otel_enabled:
        return
    resource = Resource.create({"service.name": settings.otel_service_name, "deployment.environment.name": settings.environment})
    tracer_provider = TracerProvider(resource=resource)
    tracer_provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=settings.otel_exporter_otlp_endpoint, insecure=settings.otel_insecure)))
    trace.set_tracer_provider(tracer_provider)
    reader = PeriodicExportingMetricReader(ConsoleMetricExporter())
    meter_provider = MeterProvider(resource=resource, metric_readers=[reader])
    metrics.set_meter_provider(meter_provider)
    meter = metrics.get_meter(settings.otel_service_name)
    REQUEST_COUNTER = meter.create_counter("gitlab_webhook_requests_total")
    QUEUE_COUNTER = meter.create_counter("gitlab_queue_events_total")
    JIRA_COUNTER = meter.create_counter("jira_operations_total")


def tracer(name: str):
    return trace.get_tracer(name)


@contextmanager
def span(name: str):
    with tracer("gitlab-jira-manual-hook").start_as_current_span(name) as current:
        yield current
