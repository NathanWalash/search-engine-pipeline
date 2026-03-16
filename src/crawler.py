"""Crawler utilities for fetching and traversing pages."""

from dataclasses import dataclass
from typing import Optional

import requests


@dataclass(frozen=True)
class FetchResult:
    """Represents the outcome of a single HTTP fetch attempt."""

    url: str
    ok: bool
    status_code: Optional[int]
    content: str
    error: Optional[str]


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
