"""Build pipeline orchestration for crawl -> parse -> index."""

from typing import Optional, Sequence

from src.crawler import CrawledPage, PoliteRequester, crawl_site_bfs
from src.indexer import InvertedIndex, create_inverted_index
from src.parser import parse_html

DEFAULT_START_URL = "https://quotes.toscrape.com/"
DEFAULT_ALLOWED_DOMAIN = "quotes.toscrape.com"


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
    timeout_seconds: float = 10.0,
    user_agent: str = "search-engine-pipeline/1.0",
    max_pages: Optional[int] = None,
) -> tuple[InvertedIndex, list[CrawledPage]]:
    """Run the full crawl+index pipeline and return the built index."""
    pages = crawl_site_bfs(
        start_url,
        allowed_domain=allowed_domain,
        requester=requester,
        timeout_seconds=timeout_seconds,
        user_agent=user_agent,
        max_pages=max_pages,
    )
    index = index_crawled_pages(pages)
    return index, list(pages)
