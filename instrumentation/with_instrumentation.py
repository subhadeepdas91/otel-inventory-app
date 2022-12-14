import inspect
from functools import wraps
from typing import Callable

from opentelemetry import trace


def with_instrumentation(fn: Callable):
    @wraps(fn)
    async def __otel_wrap(*args, **kwargs):
        tracer = trace.get_tracer(__name__)
        with tracer.start_as_current_span(f"{fn.__module__}.{fn.__name__}") as span:
            span.set_attribute("operation.module", f"{fn.__module__}.{fn.__name__}")
            for idx, a in enumerate(args):
                span.set_attribute(f"operation.arg_{idx}_value", str(a))
                span.set_attribute(f"operation.args_{idx}_type", str(type(a)))
            for k, v in kwargs.items():
                span.set_attribute(f"operation.kwarg_{k}_value", str(v))
                span.set_attribute(f"operation.kwarg_{k}_type", str(type(v)))
            try:
                result = fn(*args, **kwargs)
                if inspect.iscoroutine(result):
                    result = await result
                span.set_attribute("operation.result_value", str(result))
                span.set_attribute("operation.result_type", str(type(result)))
                return result
            except Exception as e:
                span.set_status(trace.StatusCode.ERROR)
                span.record_exception(e)
                raise e

    return __otel_wrap
