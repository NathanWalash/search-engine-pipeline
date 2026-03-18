"""Build pipeline orchestration for crawl -> parse -> index."""

from dataclasses import dataclass
import hashlib
import re
import time
from typing import Callable, Optional, Sequence

from src.crawler import (
    CrawlReport,
    CrawledPage,
    PoliteRequester,
    crawl_site_bfs_with_report,
)
from src.indexer import (
    InvertedIndex,
    PostingRecord,
    TermRecord,
    create_inverted_index,
)
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
    documents_reused: int = 0
    documents_reindexed: int = 0
    documents_new: int = 0


@dataclass(frozen=True)
class BuildResult:
    """Final index plus summary data produced by build."""

    index: InvertedIndex
    pages: list[CrawledPage]
    summary: BuildSummary
    crawl_report: Optional[CrawlReport] = None


@dataclass(frozen=True)
class IncrementalIndexStats:
    """Counts describing incremental indexing reuse behavior."""

    documents_reused: int = 0
    documents_reindexed: int = 0
    documents_new: int = 0


_DOC_ID_PATTERN = re.compile(r"^doc(\d+)$")


def _hash_page_html(html: str) -> str:
    """Return a deterministic content hash for one crawled page body."""
    return hashlib.sha1(html.encode("utf-8")).hexdigest()


def _document_number(document_id: str) -> int:
    """Return numeric suffix for doc IDs like 'doc42', else 0."""
    matched = _DOC_ID_PATTERN.match(document_id)
    if matched is None:
        return 0
    return int(matched.group(1))


def _collect_postings_by_document(
    index: InvertedIndex,
) -> dict[str, list[tuple[str, PostingRecord]]]:
    """Return term postings grouped by document ID."""
    grouped: dict[str, list[tuple[str, PostingRecord]]] = {}
    for term, term_record in index.terms.items():
        for document_id, posting in term_record.postings.items():
            grouped.setdefault(document_id, []).append((term, posting))
    return grouped


def _reuse_document_postings(
    *,
    source_index: InvertedIndex,
    target_index: InvertedIndex,
    source_document_id: str,
    target_document_id: str,
    postings_by_document: dict[str, list[tuple[str, PostingRecord]]],
) -> None:
    """Copy one unchanged document and all postings into target_index."""
    source_document = source_index.documents[source_document_id]
    target_index._register_document(
        document_id=target_document_id,
        url=source_document.url,
        token_count=source_document.length,
        text=source_document.text,
        content_hash=source_document.content_hash,
    )

    for term, posting in postings_by_document.get(source_document_id, []):
        term_record = target_index.terms.setdefault(term, TermRecord())
        term_record.postings[target_document_id] = PostingRecord(
            term_frequency=posting.term_frequency,
            positions=list(posting.positions),
        )
        term_record.document_frequency = len(term_record.postings)


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
            text=parsed.text,
            content_hash=_hash_page_html(page.html),
        )
    return index


def index_crawled_pages_incremental(
    pages: Sequence[CrawledPage],
    *,
    existing_index: InvertedIndex,
) -> tuple[InvertedIndex, IncrementalIndexStats]:
    """Build index using reuse for unchanged pages from an existing index."""
    index = create_inverted_index()
    url_to_document_id = {
        document.url: document_id
        for document_id, document in existing_index.documents.items()
    }
    postings_by_document = _collect_postings_by_document(existing_index)

    next_document_number = max(
        (_document_number(document_id) for document_id in existing_index.documents),
        default=0,
    )

    reused = 0
    reindexed = 0
    created = 0

    for page in pages:
        content_hash = _hash_page_html(page.html)
        existing_document_id = url_to_document_id.get(page.url)
        if existing_document_id is not None:
            existing_document = existing_index.documents[existing_document_id]
            if (
                existing_document.content_hash
                and existing_document.content_hash == content_hash
            ):
                _reuse_document_postings(
                    source_index=existing_index,
                    target_index=index,
                    source_document_id=existing_document_id,
                    target_document_id=existing_document_id,
                    postings_by_document=postings_by_document,
                )
                reused += 1
                continue

            document_id = existing_document_id
            reindexed += 1
        else:
            next_document_number += 1
            document_id = f"doc{next_document_number}"
            created += 1

        parsed = parse_html(page.html)
        index.add_document(
            document_id=document_id,
            url=page.url,
            token_positions=parsed.token_positions,
            text=parsed.text,
            content_hash=content_hash,
        )

    return index, IncrementalIndexStats(
        documents_reused=reused,
        documents_reindexed=reindexed,
        documents_new=created,
    )


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
    incremental: bool = False,
    existing_index: Optional[InvertedIndex] = None,
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

    incremental_stats = IncrementalIndexStats()
    if incremental and existing_index is not None:
        progress("Build: indexing crawled pages (incremental mode)...")
        index, incremental_stats = index_crawled_pages_incremental(
            pages,
            existing_index=existing_index,
        )
    else:
        progress("Build: indexing crawled pages...")
        index = index_crawled_pages(pages)
        incremental_stats = IncrementalIndexStats(
            documents_reused=0,
            documents_reindexed=len(pages),
            documents_new=0,
        )

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
        documents_reused=incremental_stats.documents_reused,
        documents_reindexed=incremental_stats.documents_reindexed,
        documents_new=incremental_stats.documents_new,
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
        f"Documents reused: {summary.documents_reused}\n"
        f"Documents reindexed: {summary.documents_reindexed}\n"
        f"Documents new: {summary.documents_new}\n"
        f"Unique terms: {summary.unique_terms}\n"
        f"Total tokens: {summary.token_count}\n"
        f"Duration: {summary.duration_seconds:.2f}s"
    )
