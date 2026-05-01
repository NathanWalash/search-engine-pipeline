"""Crawler utilities for fetching and traversing pages."""

from collections import deque
from dataclasses import dataclass
from html.parser import HTMLParser
import logging
import time
from typing import Callable, Optional
from urllib.parse import urljoin, urlparse, urlunparse

import requests

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class FetchResult:
    """Represents the outcome of a single HTTP fetch attempt."""

    url: str
    ok: bool
    status_code: Optional[int]
    content: str
    error: Optional[str]


@dataclass(frozen=True)
class CrawledPage:
    """Represents a successfully crawled page."""

    url: str
    html: str
    status_code: int


@dataclass(frozen=True)
class CrawlReport:
    """Summary statistics produced by one crawl run."""

    urls_discovered: int
    urls_visited: int
    pages_crawled: int
    pages_failed: int


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


class _HrefExtractor(HTMLParser):
    """Collect href values from anchor tags."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.hrefs: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "a":
            return

        for key, value in attrs:
            if key == "href" and value:
                self.hrefs.append(value)
                return


def normalize_url(base_url: str, href: str) -> str:
    """Resolve a raw href against base_url and strip fragments."""
    absolute = urljoin(base_url, href)
    parsed = urlparse(absolute)
    cleaned = parsed._replace(fragment="")
    return urlunparse(cleaned)


def is_internal_url(url: str, allowed_domain: str) -> bool:
    """Return whether a URL belongs to the crawl domain."""
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        return False
    hostname = (parsed.hostname or "").lower()
    allowed = allowed_domain.lower()
    return hostname == allowed or hostname.endswith(f".{allowed}")


def extract_internal_links(
    html: str,
    *,
    base_url: str,
    allowed_domain: str,
) -> list[str]:
    """Extract internal links from HTML, preserving first-seen order."""
    parser = _HrefExtractor()
    parser.feed(html)
    parser.close()

    links: list[str] = []
    seen: set[str] = set()
    for href in parser.hrefs:
        normalized = normalize_url(base_url, href)
        if not is_internal_url(normalized, allowed_domain):
            continue
        if normalized in seen:
            continue
        seen.add(normalized)
        links.append(normalized)

    return links


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
    except Exception as exc:  # pragma: no cover - defensive guard
        return FetchResult(
            url=url,
            ok=False,
            status_code=None,
            content="",
            error=f"Unexpected error: {exc}",
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


def _crawl_site_bfs_internal(
    start_url: str,
    *,
    allowed_domain: str,
    requester: Optional[PoliteRequester] = None,
    min_delay_seconds: float = 6.0,
    timeout_seconds: float = 10.0,
    user_agent: str = "search-engine-pipeline/1.0",
    max_pages: Optional[int] = None,
    progress_callback: Optional[Callable[[str], None]] = None,
) -> tuple[list[CrawledPage], CrawlReport]:
    """Crawl internal pages from start_url and collect crawl statistics."""
    fetcher = requester or PoliteRequester(min_delay_seconds=min_delay_seconds)
    progress = progress_callback or (lambda message: None)
    queue: deque[str] = deque([start_url])
    visited: set[str] = set()
    # 'scheduled' tracks URLs already added to the queue, preventing duplicates
    # before they have been visited. 'visited' prevents re-processing after fetch.
    scheduled: set[str] = {start_url}
    crawled_pages: list[CrawledPage] = []
    pages_failed = 0

    while queue:
        if max_pages is not None and len(crawled_pages) >= max_pages:
            break

        url = queue.popleft()
        if url in visited:
            continue
        visited.add(url)

        try:
            result = fetcher.fetch(
                url,
                timeout_seconds=timeout_seconds,
                user_agent=user_agent,
            )
        except Exception as exc:  # pragma: no cover - defensive guard
            LOGGER.warning("Crawler fetch raised for %s: %s", url, exc)
            pages_failed += 1
            continue

        if not result.ok:
            LOGGER.warning(
                "Crawler skipped %s due to fetch failure: %s",
                url,
                result.error or "unknown error",
            )
            pages_failed += 1
            continue

        status_code = result.status_code if result.status_code is not None else 200
        crawled_pages.append(
            CrawledPage(
                url=url,
                html=result.content,
                status_code=status_code,
            )
        )
        progress(f"Build: crawled {len(crawled_pages)} page(s) (last: {url})")

        try:
            links = extract_internal_links(
                result.content,
                base_url=url,
                allowed_domain=allowed_domain,
            )
        except Exception as exc:  # pragma: no cover - defensive guard
            LOGGER.warning("Crawler link extraction failed for %s: %s", url, exc)
            continue

        for link in links:
            if link in visited or link in scheduled:
                continue
            queue.append(link)
            scheduled.add(link)

    report = CrawlReport(
        urls_discovered=len(scheduled),
        urls_visited=len(visited),
        pages_crawled=len(crawled_pages),
        pages_failed=pages_failed,
    )
    return crawled_pages, report


def crawl_site_bfs(
    start_url: str,
    *,
    allowed_domain: str,
    requester: Optional[PoliteRequester] = None,
    min_delay_seconds: float = 6.0,
    timeout_seconds: float = 10.0,
    user_agent: str = "search-engine-pipeline/1.0",
    max_pages: Optional[int] = None,
    progress_callback: Optional[Callable[[str], None]] = None,
) -> list[CrawledPage]:
    """Crawl internal pages from start_url using BFS traversal."""
    pages, _ = _crawl_site_bfs_internal(
        start_url,
        allowed_domain=allowed_domain,
        requester=requester,
        min_delay_seconds=min_delay_seconds,
        timeout_seconds=timeout_seconds,
        user_agent=user_agent,
        max_pages=max_pages,
        progress_callback=progress_callback,
    )
    return pages


def crawl_site_bfs_with_report(
    start_url: str,
    *,
    allowed_domain: str,
    requester: Optional[PoliteRequester] = None,
    min_delay_seconds: float = 6.0,
    timeout_seconds: float = 10.0,
    user_agent: str = "search-engine-pipeline/1.0",
    max_pages: Optional[int] = None,
    progress_callback: Optional[Callable[[str], None]] = None,
) -> tuple[list[CrawledPage], CrawlReport]:
    """Crawl internal pages and return both pages and crawl report."""
    return _crawl_site_bfs_internal(
        start_url,
        allowed_domain=allowed_domain,
        requester=requester,
        min_delay_seconds=min_delay_seconds,
        timeout_seconds=timeout_seconds,
        user_agent=user_agent,
        max_pages=max_pages,
        progress_callback=progress_callback,
    )
