"""Build pipeline orchestration for crawl -> parse -> index."""

from typing import Sequence

from src.crawler import CrawledPage
from src.indexer import InvertedIndex, create_inverted_index
from src.parser import parse_html


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
