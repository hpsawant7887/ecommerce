import os

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor


class OtelTracer:
    def __init__(self, service_name):
        self.tracer = None
        
        # Configure the tracer provider
        trace.set_tracer_provider(TracerProvider())
        self.tracer = trace.get_tracer(service_name)

        # Create an OTLP Span Exporter
        otlp_exporter = OTLPSpanExporter(
        endpoint=os.environ.get("OTEL_EXPORTER_OTLP_TRACES_ENDPOINT", "http://localhost:4317"))

        # Add the exporter to the tracer provider
        trace.get_tracer_provider().add_span_processor(
            BatchSpanProcessor(otlp_exporter)
        )




