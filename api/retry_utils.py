import asyncio
import httpx
from typing import Optional, Callable, Any

class RetryConfig:
    def __init__(self, max_retries: int = 3, base_delay: float = 1.0, max_delay: float = 30.0):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay

async def fetch_with_retry(url: str, config: Optional[RetryConfig] = None) -> dict:
    cfg = config or RetryConfig()
    async with httpx.AsyncClient(timeout=30.0) as client:
        for attempt in range(cfg.max_retries):
            try:
                resp = await client.get(url)
                resp.raise_for_status()
                return {"success": True, "content": resp.text, "status": resp.status_code}
            except httpx.HTTPStatusError as e:
                if e.response.status_code < 500:
                    return {"success": False, "error": str(e), "status": e.response.status_code}
                if attempt == cfg.max_retries - 1:
                    return {"success": False, "error": str(e), "status": e.response.status_code}
                delay = min(cfg.base_delay * (2 ** attempt), cfg.max_delay)
                await asyncio.sleep(delay)
            except (httpx.ConnectError, httpx.TimeoutException, httpx.RemoteProtocolError) as e:
                if attempt == cfg.max_retries - 1:
                    return {"success": False, "error": str(e), "status": 0}
                delay = min(cfg.base_delay * (2 ** attempt), cfg.max_delay)
                await asyncio.sleep(delay)
    return {"success": False, "error": "Max retries exceeded", "status": 0}

async def retry_with_backoff(fn: Callable[[], Any], config: Optional[RetryConfig] = None) -> Any:
    cfg = config or RetryConfig()
    last_exc = None
    for attempt in range(cfg.max_retries):
        try:
            return await fn()
        except Exception as e:
            last_exc = e
            if attempt == cfg.max_retries - 1:
                raise
            delay = min(cfg.base_delay * (2 ** attempt), cfg.max_delay)
            await asyncio.sleep(delay)
