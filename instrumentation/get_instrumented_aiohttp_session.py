import aiohttp
from opentelemetry.instrumentation.aiohttp_client import create_trace_config
from functools import lru_cache

@lru_cache
def get_instrumented_aiohttp_session() -> aiohttp.ClientSession:
    return aiohttp.ClientSession(
        trace_configs=[create_trace_config()]
    )
