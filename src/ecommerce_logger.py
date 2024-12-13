import logging
from opentelemetry.instrumentation.logging import LoggingInstrumentor


class OptionalFieldFormatter(logging.Formatter):
    def format(self, record):
        if not hasattr(record, 'otelTraceID'):
            record.otelTraceID = 'N/A'
        
        if not hasattr(record, 'otelSpanID'):
            record.otelTraceID = 'N/A'
        return super().format(record)
    

def set_logger():
    logger = logging.getLogger(__name__)
    handler = logging.StreamHandler()
    formatter = OptionalFieldFormatter('%(asctime)s - %(name)s - %(levelname)s - [trace_id=%(otelTraceID)s span_id=%(otelSpanID)s] - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)

    LoggingInstrumentor().instrument()

    return logger