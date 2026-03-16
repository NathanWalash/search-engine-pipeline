"""Query helpers for term lookup and result formatting."""

from dataclasses import dataclass
from typing import Optional

from src.indexer import InvertedIndex


@dataclass(frozen=True)
class TermPostingView:
    """Renderable posting data for one document match."""

    document_id: str
    url: str
    term_frequency: int
    positions: list[int]


@dataclass(frozen=True)
class TermLookupView:
    """Renderable lookup data for one indexed term."""

    term: str
    document_frequency: int
    postings: list[TermPostingView]


def lookup_term(index: InvertedIndex, raw_term: str) -> Optional[TermLookupView]:
    """Return lookup data for one term, or None if term is not indexed."""
    term = raw_term.lower()
    term_record = index.terms.get(term)
    if term_record is None:
        return None

    postings: list[TermPostingView] = []
    for document_id, posting in term_record.postings.items():
        document = index.documents.get(document_id)
        postings.append(
            TermPostingView(
                document_id=document_id,
                url=document.url if document is not None else "",
                term_frequency=posting.term_frequency,
                positions=list(posting.positions),
            )
        )

    return TermLookupView(
        term=term,
        document_frequency=term_record.document_frequency,
        postings=postings,
    )


def format_term_lookup(result: TermLookupView) -> str:
    """Render one term lookup as user-facing text output."""
    lines = [
        f"Word: {result.term}",
        f"Document frequency: {result.document_frequency}",
    ]

    for posting in result.postings:
        lines.append(
            (
                f"- {posting.document_id} | {posting.url} | "
                f"term_frequency={posting.term_frequency} | "
                f"positions={posting.positions}"
            )
        )

    return "\n".join(lines)
