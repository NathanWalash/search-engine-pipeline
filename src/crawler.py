"""Crawler utilities for fetching and traversing pages."""

from dataclasses import dataclass
import time
from typing import Callable, Optional

import requests


@dataclass(frozen=True)
class FetchResult:
    """Represents the outcome of a single HTTP fetch attempt."""

    url: str
    ok: bool
    status_code: Optional[int]
    content: str
    error: Optional[str]


class PoliteRequester:
    """Enforces a minimum delay between successive HTTP requests."""

    def __init__(
        self,
        *,
        min_delay_seconds: float = 6.0,
        clock: Callable[[], float] = time.monotonic,
        sleeper: Callable[[float], None] = time.sleep,
    ) -> None:
        self._min_delay_seconds = min_delay_seconds
        self._clock = clock
        self._sleeper = sleeper
        self._last_request_time: Optional[float] = None

    def _wait_if_needed(self) -> None:
        if self._last_request_time is None:
            return

        elapsed = self._clock() - self._last_request_time
        remaining = self._min_delay_seconds - elapsed
        if remaining > 0:
            self._sleeper(remaining)

    def fetch(
        self,
        url: str,
        *,
        timeout_seconds: float = 10.0,
        user_agent: str = "search-engine-pipeline/1.0",
    ) -> FetchResult:
        """Wait for the politeness window, then fetch the target URL."""
        self._wait_if_needed()
        result = fetch_page(
            url,
            timeout_seconds=timeout_seconds,
            user_agent=user_agent,
        )
        self._last_request_time = self._clock()
        return result


def fetch_page(
    url: str,
    *,
    timeout_seconds: float = 10.0,
    user_agent: str = "search-engine-pipeline/1.0",
) -> FetchResult:
    """Fetch a page and return a structured success/error result."""
    headers = {"User-Agent": user_agent}
    try:
        response = requests.get(url, timeout=timeout_seconds, headers=headers)
    except requests.RequestException as exc:
        return FetchResult(
            url=url,
            ok=False,
            status_code=None,
            content="",
            error=str(exc),
        )

    if response.status_code >= 400:
        return FetchResult(
            url=url,
            ok=False,
            status_code=response.status_code,
            content="",
            error=f"HTTP {response.status_code}",
        )

    return FetchResult(
        url=url,
        ok=True,
        status_code=response.status_code,
        content=response.text,
        error=None,
    )
