"""Integration-style tests for the build pipeline module."""

import src.build_pipeline as build_pipeline
from src.crawler import CrawlReport, CrawledPage


def test_index_crawled_pages_builds_index_from_html() -> None:
    pages = [
        CrawledPage(
            url="https://quotes.toscrape.com/page/1/",
            html="<p>Good friends make good times</p>",
            status_code=200,
        ),
        CrawledPage(
            url="https://quotes.toscrape.com/page/2/",
            html="<p>Truth and kindness</p>",
            status_code=200,
        ),
    ]

    index = build_pipeline.index_crawled_pages(pages)
    serialised = index.to_dict()

    assert serialised["meta"]["page_count"] == 2
    assert serialised["documents"]["doc1"]["url"] == "https://quotes.toscrape.com/page/1/"
    assert "Good friends make good times" in serialised["documents"]["doc1"]["text"]
    assert serialised["terms"]["good"]["document_frequency"] == 1
    assert serialised["terms"]["good"]["postings"]["doc1"]["term_frequency"] == 2
    assert serialised["terms"]["truth"]["document_frequency"] == 1


def test_run_build_pipeline_uses_crawl_output(monkeypatch) -> None:
    pages = [
        CrawledPage(
            url="https://quotes.toscrape.com/",
            html="<p>One two one</p>",
            status_code=200,
        )
    ]

    def fake_crawl_site_bfs_with_report(
        start_url: str,
        *,
        allowed_domain: str,
        requester,
        min_delay_seconds: float,
        timeout_seconds: float,
        user_agent: str,
        max_pages,
        progress_callback,
    ) -> list[CrawledPage]:
        assert start_url == "https://quotes.toscrape.com/"
        assert allowed_domain == "quotes.toscrape.com"
        assert requester is None
        assert min_delay_seconds == 6.0
        assert timeout_seconds == 10.0
        assert user_agent == "search-engine-pipeline/1.0"
        assert max_pages is None
        assert callable(progress_callback)
        return pages, CrawlReport(
            urls_discovered=3,
            urls_visited=2,
            pages_crawled=1,
            pages_failed=1,
        )

    monkeypatch.setattr(
        build_pipeline,
        "crawl_site_bfs_with_report",
        fake_crawl_site_bfs_with_report,
    )
    progress_messages: list[str] = []
    result = build_pipeline.run_build_pipeline(progress_callback=progress_messages.append)
    index = result.index
    crawled_pages = result.pages

    assert [page.url for page in crawled_pages] == ["https://quotes.toscrape.com/"]
    serialised = index.to_dict()
    assert serialised["meta"] == {"page_count": 1, "token_count": 3}
    assert serialised["terms"]["one"]["postings"]["doc1"]["positions"] == [0, 2]
    assert result.summary.pages_failed == 1
    assert result.summary.urls_discovered == 3
    assert result.summary.urls_visited == 2
    assert result.summary.crawl_success_rate == 0.5
    assert progress_messages == [
        "Build: crawling pages...",
        "Build: indexing crawled pages...",
        "Build: complete.",
    ]


def test_format_build_summary_is_deterministic() -> None:
    summary = build_pipeline.BuildSummary(
        pages_crawled=3,
        unique_terms=12,
        token_count=87,
        duration_seconds=1.23456,
    )

    assert build_pipeline.format_build_summary(summary) == (
        "Build complete.\n"
        "Pages crawled: 3\n"
        "Pages failed: 0\n"
        "URLs discovered: 0\n"
        "URLs visited: 0\n"
        "Crawl success rate: 0.0%\n"
        "Unique terms: 12\n"
        "Total tokens: 87\n"
        "Duration: 1.23s"
    )
