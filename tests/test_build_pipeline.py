"""Integration-style tests for the build pipeline module."""

import src.build_pipeline as build_pipeline
from src.crawler import CrawledPage


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

    def fake_crawl_site_bfs(
        start_url: str,
        *,
        allowed_domain: str,
        requester,
        timeout_seconds: float,
        user_agent: str,
        max_pages,
    ) -> list[CrawledPage]:
        assert start_url == "https://quotes.toscrape.com/"
        assert allowed_domain == "quotes.toscrape.com"
        assert requester is None
        assert timeout_seconds == 10.0
        assert user_agent == "search-engine-pipeline/1.0"
        assert max_pages is None
        return pages

    monkeypatch.setattr(build_pipeline, "crawl_site_bfs", fake_crawl_site_bfs)
    progress_messages: list[str] = []
    result = build_pipeline.run_build_pipeline(progress_callback=progress_messages.append)
    index = result.index
    crawled_pages = result.pages

    assert [page.url for page in crawled_pages] == ["https://quotes.toscrape.com/"]
    serialised = index.to_dict()
    assert serialised["meta"] == {"page_count": 1, "token_count": 3}
    assert serialised["terms"]["one"]["postings"]["doc1"]["positions"] == [0, 2]
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
        "Unique terms: 12\n"
        "Total tokens: 87\n"
        "Duration: 1.23s"
    )
