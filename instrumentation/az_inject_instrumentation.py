import os

from azure.monitor.opentelemetry.exporter import AzureMonitorTraceExporter
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.trace.sampling import ParentBasedTraceIdRatio
from starlette.types import ASGIApp


def inject_instrumentation(app: ASGIApp) -> None:
    # For Manual Instrumentation guide
    # https://opentelemetry.io/docs/instrumentation/python/manual/

    # Setup resource to be shown in traces
    # https://opentelemetry.io/docs/reference/specification/resource/semantic_conventions/
    resource = Resource.create(
        attributes={
            "service.name": os.environ.get("OTEL_SERVICE_NAME", "backend"),
            "service.version": "0.0.0",
        }
    )
    # set the tracer provider
    # https://opentelemetry.io/docs/reference/specification/trace/api/#tracerprovider
    # For Sampling
    # https://opentelemetry-python.readthedocs.io/en/latest/sdk/trace.sampling.html
    tracer = TracerProvider(resource=resource, sampler=ParentBasedTraceIdRatio(1))

    trace.set_tracer_provider(tracer)

    exporter = AzureMonitorTraceExporter(
        connection_string=os.environ.get("APPINSIGHT_CONNECTION_STRING"),
    )
    span_processor = BatchSpanProcessor(exporter)
    trace.get_tracer_provider().add_span_processor(span_processor)

    LoggingInstrumentor().instrument(set_logging_format=True)
    FastAPIInstrumentor.instrument_app(app, tracer_provider=tracer)
