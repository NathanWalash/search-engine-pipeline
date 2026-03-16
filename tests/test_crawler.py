"""Unit tests for crawler request, link, and BFS traversal logic."""

from __future__ import annotations

from dataclasses import dataclass

import requests

import src.crawler as crawler


@dataclass
class _FakeResponse:
    status_code: int
    text: str


def test_fetch_page_success(monkeypatch) -> None:
    def fake_get(url: str, timeout: float, headers: dict[str, str]) -> _FakeResponse:
        assert url == "https://quotes.toscrape.com/"
        assert timeout == 5.0
        assert headers["User-Agent"] == "ua-test"
        return _FakeResponse(status_code=200, text="<html>ok</html>")

    monkeypatch.setattr(crawler.requests, "get", fake_get)
    result = crawler.fetch_page(
        "https://quotes.toscrape.com/",
        timeout_seconds=5.0,
        user_agent="ua-test",
    )

    assert result.ok is True
    assert result.status_code == 200
    assert result.content == "<html>ok</html>"
    assert result.error is None


def test_fetch_page_http_error(monkeypatch) -> None:
    monkeypatch.setattr(
        crawler.requests,
        "get",
        lambda *args, **kwargs: _FakeResponse(status_code=500, text="error"),
    )
    result = crawler.fetch_page("https://quotes.toscrape.com/fail")

    assert result.ok is False
    assert result.status_code == 500
    assert result.content == ""
    assert result.error == "HTTP 500"


def test_fetch_page_request_exception(monkeypatch) -> None:
    def fake_get(*args, **kwargs):
        raise requests.Timeout("timed out")

    monkeypatch.setattr(crawler.requests, "get", fake_get)
    result = crawler.fetch_page("https://quotes.toscrape.com/timeout")

    assert result.ok is False
    assert result.status_code is None
    assert result.content == ""
    assert "timed out" in (result.error or "")


def test_extract_internal_links_filters_and_deduplicates() -> None:
    html = """
    <a href="/page/2/">next</a>
    <a href="https://quotes.toscrape.com/page/2/">dup</a>
    <a href="https://quotes.toscrape.com/page/3/#frag">fragment</a>
    <a href="https://example.com/outside">outside</a>
    <a href="mailto:test@example.com">email</a>
    """

    links = crawler.extract_internal_links(
        html,
        base_url="https://quotes.toscrape.com/page/1/",
        allowed_domain="quotes.toscrape.com",
    )

    assert links == [
        "https://quotes.toscrape.com/page/2/",
        "https://quotes.toscrape.com/page/3/",
    ]


def test_polite_requester_waits_between_requests(monkeypatch) -> None:
    clock_values = iter([0.0, 2.0, 3.0])
    sleep_calls: list[float] = []

    def fake_clock() -> float:
        return next(clock_values)

    def fake_sleep(seconds: float) -> None:
        sleep_calls.append(seconds)

    def fake_fetch_page(
        url: str,
        *,
        timeout_seconds: float = 10.0,
        user_agent: str = "search-engine-pipeline/1.0",
    ) -> crawler.FetchResult:
        del timeout_seconds, user_agent
        return crawler.FetchResult(
            url=url,
            ok=True,
            status_code=200,
            content="<html></html>",
            error=None,
        )

    monkeypatch.setattr(crawler, "fetch_page", fake_fetch_page)
    requester = crawler.PoliteRequester(
        min_delay_seconds=6.0,
        clock=fake_clock,
        sleeper=fake_sleep,
    )

    requester.fetch("https://quotes.toscrape.com/")
    requester.fetch("https://quotes.toscrape.com/page/2/")

    assert sleep_calls == [4.0]


class _FakeRequester:
    def __init__(self, responses: dict[str, crawler.FetchResult]) -> None:
        self._responses = responses
        self.requested_urls: list[str] = []

    def fetch(self, url: str, **kwargs) -> crawler.FetchResult:
        del kwargs
        self.requested_urls.append(url)
        return self._responses[url]


def test_crawl_site_bfs_visits_internal_pages_once() -> None:
    start = "https://quotes.toscrape.com/"
    page_2 = "https://quotes.toscrape.com/page/2/"
    responses = {
        start: crawler.FetchResult(
            url=start,
            ok=True,
            status_code=200,
            content=(
                '<a href="/page/2/">to-page-2</a>'
                '<a href="/page/2/">duplicate-link</a>'
                '<a href="https://example.com">external</a>'
            ),
            error=None,
        ),
        page_2: crawler.FetchResult(
            url=page_2,
            ok=True,
            status_code=200,
            content='<a href="/">back-home</a>',
            error=None,
        ),
    }
    requester = _FakeRequester(responses)

    pages = crawler.crawl_site_bfs(
        start,
        allowed_domain="quotes.toscrape.com",
        requester=requester,  # type: ignore[arg-type]
    )

    assert [page.url for page in pages] == [start, page_2]
    assert requester.requested_urls == [start, page_2]


def test_crawl_site_bfs_skips_failed_pages() -> None:
    start = "https://quotes.toscrape.com/"
    missing = "https://quotes.toscrape.com/missing/"
    responses = {
        start: crawler.FetchResult(
            url=start,
            ok=True,
            status_code=200,
            content='<a href="/missing/">broken</a>',
            error=None,
        ),
        missing: crawler.FetchResult(
            url=missing,
            ok=False,
            status_code=404,
            content="",
            error="HTTP 404",
        ),
    }
    requester = _FakeRequester(responses)

    pages = crawler.crawl_site_bfs(
        start,
        allowed_domain="quotes.toscrape.com",
        requester=requester,  # type: ignore[arg-type]
    )

    assert [page.url for page in pages] == [start]
    assert requester.requested_urls == [start, missing]
