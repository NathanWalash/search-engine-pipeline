"""Build pipeline orchestration for crawl -> parse -> index."""

from dataclasses import dataclass
import time
from typing import Callable, Optional, Sequence

from src.crawler import (
    CrawlReport,
    CrawledPage,
    PoliteRequester,
    crawl_site_bfs_with_report,
)
from src.indexer import InvertedIndex, create_inverted_index
from src.parser import parse_html

DEFAULT_START_URL = "https://quotes.toscrape.com/"
DEFAULT_ALLOWED_DOMAIN = "quotes.toscrape.com"


@dataclass(frozen=True)
class BuildSummary:
    """High-level metrics produced by one build run."""

    pages_crawled: int
    unique_terms: int
    token_count: int
    duration_seconds: float
    pages_failed: int = 0
    urls_discovered: int = 0
    urls_visited: int = 0
    crawl_success_rate: float = 0.0


@dataclass(frozen=True)
class BuildResult:
    """Final index plus summary data produced by build."""

    index: InvertedIndex
    pages: list[CrawledPage]
    summary: BuildSummary
    crawl_report: Optional[CrawlReport] = None


def index_crawled_pages(pages: Sequence[CrawledPage]) -> InvertedIndex:
    """Convert crawled HTML pages into an in-memory inverted index."""
    index = create_inverted_index()
    for document_number, page in enumerate(pages, start=1):
        document_id = f"doc{document_number}"
        parsed = parse_html(page.html)
        index.add_document(
            document_id=document_id,
            url=page.url,
            token_positions=parsed.token_positions,
        )
    return index


def run_build_pipeline(
    *,
    start_url: str = DEFAULT_START_URL,
    allowed_domain: str = DEFAULT_ALLOWED_DOMAIN,
    requester: Optional[PoliteRequester] = None,
    min_delay_seconds: float = 6.0,
    timeout_seconds: float = 10.0,
    user_agent: str = "search-engine-pipeline/1.0",
    max_pages: Optional[int] = None,
    progress_callback: Optional[Callable[[str], None]] = None,
) -> BuildResult:
    """Run the full crawl+index pipeline and return the built index."""
    progress = progress_callback or (lambda message: None)
    started_at = time.monotonic()

    progress("Build: crawling pages...")
    pages, crawl_report = crawl_site_bfs_with_report(
        start_url,
        allowed_domain=allowed_domain,
        requester=requester,
        min_delay_seconds=min_delay_seconds,
        timeout_seconds=timeout_seconds,
        user_agent=user_agent,
        max_pages=max_pages,
        progress_callback=progress,
    )

    progress("Build: indexing crawled pages...")
    index = index_crawled_pages(pages)
    duration_seconds = time.monotonic() - started_at
    crawl_success_rate = (
        crawl_report.pages_crawled / crawl_report.urls_visited
        if crawl_report.urls_visited
        else 0.0
    )

    summary = BuildSummary(
        pages_crawled=len(pages),
        unique_terms=len(index.terms),
        token_count=index.meta["token_count"],
        duration_seconds=duration_seconds,
        pages_failed=crawl_report.pages_failed,
        urls_discovered=crawl_report.urls_discovered,
        urls_visited=crawl_report.urls_visited,
        crawl_success_rate=crawl_success_rate,
    )
    progress("Build: complete.")
    return BuildResult(
        index=index,
        pages=list(pages),
        summary=summary,
        crawl_report=crawl_report,
    )


def format_build_summary(summary: BuildSummary) -> str:
    """Render user-facing build metrics as deterministic text."""
    return (
        "Build complete.\n"
        f"Pages crawled: {summary.pages_crawled}\n"
        f"Pages failed: {summary.pages_failed}\n"
        f"URLs discovered: {summary.urls_discovered}\n"
        f"URLs visited: {summary.urls_visited}\n"
        f"Crawl success rate: {summary.crawl_success_rate:.1%}\n"
        f"Unique terms: {summary.unique_terms}\n"
        f"Total tokens: {summary.token_count}\n"
        f"Duration: {summary.duration_seconds:.2f}s"
    )
