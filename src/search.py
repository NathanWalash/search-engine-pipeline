"""Query helpers for term lookup and result formatting."""

from dataclasses import dataclass
from typing import Optional, Sequence

from src.indexer import InvertedIndex
from src.ranking import score_document_tfidf


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


@dataclass(frozen=True)
class QueryMatchView:
    """Renderable query match for one document."""

    document_id: str
    url: str
    term_frequencies: dict[str, int]
    relevance_score: float


def _normalize_query_terms(query_terms: Sequence[str]) -> list[str]:
    """Lowercase and de-duplicate query terms while preserving order."""
    normalized: list[str] = []
    seen: set[str] = set()
    for term in query_terms:
        lowered = term.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        normalized.append(lowered)
    return normalized


def lookup_term(index: InvertedIndex, raw_term: str) -> Optional[TermLookupView]:
    """Return lookup data for one term, or None if term is not indexed."""
    term = raw_term.lower()
    term_record = index.terms.get(term)
    if term_record is None:
        return None

    postings: list[TermPostingView] = []
    for document_id, posting in sorted(term_record.postings.items()):
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
        "Postings:",
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


def find_and_match_documents(
    index: InvertedIndex,
    query_terms: Sequence[str],
) -> list[QueryMatchView]:
    """Return documents that contain all query terms (AND semantics)."""
    normalized_terms = _normalize_query_terms(query_terms)
    if not normalized_terms:
        return []

    term_records = []
    for term in normalized_terms:
        term_record = index.terms.get(term)
        if term_record is None:
            return []
        term_records.append((term, term_record))

    matching_document_ids = set(term_records[0][1].postings.keys())
    for _, term_record in term_records[1:]:
        matching_document_ids &= set(term_record.postings.keys())

    matches: list[QueryMatchView] = []
    for document_id in sorted(matching_document_ids):
        document = index.documents.get(document_id)
        if document is None:
            continue

        term_frequencies = {
            term: term_record.postings[document_id].term_frequency
            for term, term_record in term_records
        }
        matches.append(
            QueryMatchView(
                document_id=document_id,
                url=document.url,
                term_frequencies=term_frequencies,
                relevance_score=score_document_tfidf(
                    index,
                    document_id=document_id,
                    query_terms=normalized_terms,
                ),
            )
        )

    matches.sort(
        key=lambda match: (-match.relevance_score, match.url, match.document_id)
    )
    return matches


def format_find_results(query_terms: Sequence[str], matches: Sequence[QueryMatchView]) -> str:
    """Render AND query matches as user-facing text output."""
    normalized_terms = _normalize_query_terms(query_terms)
    lines = [f"Query: {' '.join(normalized_terms)}", f"Matches: {len(matches)}"]

    for match in matches:
        term_stats = ", ".join(
            f"{term}={match.term_frequencies[term]}"
            for term in sorted(match.term_frequencies)
        )
        lines.append(
            (
                f"- {match.document_id} | {match.url} | "
                f"score={match.relevance_score:.4f} | {term_stats}"
            )
        )

    return "\n".join(lines)
