import logging
from logging import LogRecord
from opentelemetry import trace
from opentelemetry.trace import INVALID_SPAN, StatusCode


class InstrumentedLoggerHandler(logging.Handler):
    def emit(self, record: LogRecord) -> None:
        span = trace.get_current_span()
        if span != INVALID_SPAN:
            span.add_event(f"{record.levelname}: {record.msg}")
            if record.levelno >= 40:
                span.set_status(StatusCode.ERROR)


def get_instumented_logger(*args, **kwargs) -> logging.Logger:
    logger = logging.getLogger(*args, **kwargs)
    logger.addHandler(InstrumentedLoggerHandler())
    return logger
