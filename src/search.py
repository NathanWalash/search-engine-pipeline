"""Query helpers for term lookup and result formatting."""

from dataclasses import dataclass
import re
from typing import Mapping, Optional, Sequence

from src.indexer import InvertedIndex, TermRecord
from src.parser import tokenize
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


@dataclass(frozen=True)
class ParsedFindQuery:
    """Normalized representation of a find query."""

    terms: list[str]
    phrases: list[list[str]]
    scoring_terms: list[str]
    display_query: str


QUERY_COMPONENT_PATTERN = re.compile(r'"([^"]+)"|(\S+)')


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


def _normalize_raw_term(raw_term: str) -> str:
    """Convert raw user input into one normalized lookup term."""
    tokens = tokenize(raw_term, expand_hyphenated=False)
    if not tokens:
        return raw_term.strip().lower()
    return tokens[0]


def _levenshtein_distance(left: str, right: str) -> int:
    """Return Levenshtein edit distance between two terms."""
    if left == right:
        return 0
    if not left:
        return len(right)
    if not right:
        return len(left)

    previous = list(range(len(right) + 1))
    for left_index, left_char in enumerate(left, start=1):
        current = [left_index]
        for right_index, right_char in enumerate(right, start=1):
            insert_cost = current[right_index - 1] + 1
            delete_cost = previous[right_index] + 1
            replace_cost = previous[right_index - 1] + int(left_char != right_char)
            current.append(min(insert_cost, delete_cost, replace_cost))
        previous = current
    return previous[-1]


def suggest_closest_term(
    index: InvertedIndex,
    raw_term: str,
    *,
    max_distance: int = 2,
) -> Optional[str]:
    """Return nearest indexed term for raw_term, or None when no close match exists."""
    term = _normalize_raw_term(raw_term)
    if not term or term in index.terms:
        return None

    best_term: Optional[str] = None
    best_distance = max_distance + 1
    for candidate in index.terms:
        distance = _levenshtein_distance(term, candidate)
        if distance > max_distance:
            continue
        if distance < best_distance:
            best_term = candidate
            best_distance = distance
            continue
        if distance == best_distance and best_term is not None and candidate < best_term:
            best_term = candidate

    return best_term


def suggest_query_terms(index: InvertedIndex, query_terms: Sequence[str]) -> dict[str, str]:
    """Return missing query terms mapped to closest indexed suggestions."""
    parsed_query = _parse_find_query(query_terms)
    suggestions: dict[str, str] = {}
    for term in parsed_query.scoring_terms:
        if term in index.terms:
            continue
        suggestion = suggest_closest_term(index, term)
        if suggestion is None:
            continue
        suggestions[term] = suggestion
    return suggestions


def _parse_find_query(query_terms: Sequence[str]) -> ParsedFindQuery:
    """Parse plain terms and quoted phrases from a find query."""
    raw_query = " ".join(query_terms).strip()
    collected_terms: list[str] = []
    collected_phrases: list[list[str]] = []
    display_parts: list[str] = []
    seen_display_terms: set[str] = set()
    seen_display_phrases: set[tuple[str, ...]] = set()

    for match in QUERY_COMPONENT_PATTERN.finditer(raw_query):
        phrase_raw, token_raw = match.groups()
        if phrase_raw is not None:
            phrase_tokens = tokenize(phrase_raw, expand_hyphenated=False)
            if not phrase_tokens:
                continue
            collected_phrases.append(phrase_tokens)
            phrase_key = tuple(phrase_tokens)
            if phrase_key not in seen_display_phrases:
                display_parts.append(f"\"{' '.join(phrase_tokens)}\"")
                seen_display_phrases.add(phrase_key)
            continue

        if token_raw is None:
            continue

        for term in tokenize(token_raw, expand_hyphenated=False):
            collected_terms.append(term)
            if term not in seen_display_terms:
                display_parts.append(term)
                seen_display_terms.add(term)

    normalized_terms = _normalize_query_terms(collected_terms)
    normalized_phrases: list[list[str]] = []
    seen_phrases: set[tuple[str, ...]] = set()
    for phrase_tokens in collected_phrases:
        phrase_key = tuple(phrase_tokens)
        if phrase_key in seen_phrases:
            continue
        seen_phrases.add(phrase_key)
        normalized_phrases.append(phrase_tokens)

    phrase_terms = [term for phrase in normalized_phrases for term in phrase]
    scoring_terms = _normalize_query_terms([*normalized_terms, *phrase_terms])
    return ParsedFindQuery(
        terms=normalized_terms,
        phrases=normalized_phrases,
        scoring_terms=scoring_terms,
        display_query=" ".join(display_parts),
    )


def _resolve_query_term_records(
    index: InvertedIndex,
    query_terms: Sequence[str],
) -> Optional[dict[str, TermRecord]]:
    """Return query term records, or None if any term is missing from index."""
    term_records: dict[str, TermRecord] = {}
    for term in query_terms:
        term_record = index.terms.get(term)
        if term_record is None:
            return None
        term_records[term] = term_record
    return term_records


def _order_terms_by_document_frequency(
    term_records: Mapping[str, TermRecord],
) -> list[str]:
    """Order query terms for AND intersection by ascending document frequency."""
    return sorted(
        term_records,
        key=lambda term: (term_records[term].document_frequency, term),
    )


def _intersect_term_document_ids(
    term_records: Mapping[str, TermRecord],
    ordered_terms: Sequence[str],
) -> set[str]:
    """Return document IDs that contain all ordered terms."""
    matching_document_ids: Optional[set[str]] = None
    for term in ordered_terms:
        term_document_ids = set(term_records[term].postings)
        if matching_document_ids is None:
            matching_document_ids = term_document_ids
        else:
            matching_document_ids &= term_document_ids
        if not matching_document_ids:
            return set()
    return matching_document_ids or set()


def _document_contains_phrase(
    index: InvertedIndex,
    *,
    document_id: str,
    phrase_tokens: Sequence[str],
) -> bool:
    """Return whether phrase_tokens occur contiguously in a document."""
    if not phrase_tokens:
        return False

    position_sets: list[set[int]] = []
    for term in phrase_tokens:
        term_record = index.terms.get(term)
        if term_record is None:
            return False
        posting = term_record.postings.get(document_id)
        if posting is None:
            return False
        position_sets.append(set(posting.positions))

    first_positions = position_sets[0]
    for start_position in first_positions:
        if all(
            (start_position + offset) in position_sets[offset]
            for offset in range(1, len(position_sets))
        ):
            return True
    return False


def _find_phrase_document_ids(
    index: InvertedIndex,
    *,
    phrase_tokens: Sequence[str],
    candidate_document_ids: Optional[set[str]] = None,
) -> set[str]:
    """Return document IDs that satisfy one exact phrase."""
    if not phrase_tokens:
        return set()

    first_term_record = index.terms.get(phrase_tokens[0])
    if first_term_record is None:
        return set()

    matching_ids = set(first_term_record.postings.keys())
    if candidate_document_ids is not None:
        matching_ids &= candidate_document_ids

    for term in phrase_tokens[1:]:
        term_record = index.terms.get(term)
        if term_record is None:
            return set()
        matching_ids &= set(term_record.postings.keys())
        if not matching_ids:
            return set()

    return {
        document_id
        for document_id in matching_ids
        if _document_contains_phrase(
            index,
            document_id=document_id,
            phrase_tokens=phrase_tokens,
        )
    }


def lookup_term(index: InvertedIndex, raw_term: str) -> Optional[TermLookupView]:
    """Return lookup data for one term, or None if term is not indexed."""
    term = _normalize_raw_term(raw_term)
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
    """Return documents that satisfy AND terms and optional quoted phrases."""
    parsed_query = _parse_find_query(query_terms)
    if not parsed_query.terms and not parsed_query.phrases:
        return []

    matching_document_ids: Optional[set[str]] = None
    if parsed_query.terms:
        term_records = _resolve_query_term_records(index, parsed_query.terms)
        if term_records is None:
            return []
        ordered_terms = _order_terms_by_document_frequency(term_records)
        matching_document_ids = _intersect_term_document_ids(
            term_records,
            ordered_terms,
        )
        if not matching_document_ids:
            return []

    for phrase_tokens in parsed_query.phrases:
        phrase_document_ids = _find_phrase_document_ids(
            index,
            phrase_tokens=phrase_tokens,
            candidate_document_ids=matching_document_ids,
        )
        if not phrase_document_ids:
            return []
        if matching_document_ids is None:
            matching_document_ids = phrase_document_ids
        else:
            matching_document_ids &= phrase_document_ids
        if not matching_document_ids:
            return []

    if not matching_document_ids:
        return []

    matches: list[QueryMatchView] = []
    for document_id in sorted(matching_document_ids):
        document = index.documents.get(document_id)
        if document is None:
            continue

        term_frequencies: dict[str, int] = {}
        for term in parsed_query.scoring_terms:
            term_record = index.terms.get(term)
            if term_record is None:
                continue
            posting = term_record.postings.get(document_id)
            if posting is None:
                continue
            term_frequencies[term] = posting.term_frequency

        matches.append(
            QueryMatchView(
                document_id=document_id,
                url=document.url,
                term_frequencies=term_frequencies,
                relevance_score=score_document_tfidf(
                    index,
                    document_id=document_id,
                    query_terms=parsed_query.scoring_terms,
                ),
            )
        )

    matches.sort(
        key=lambda match: (-match.relevance_score, match.url, match.document_id)
    )
    return matches


def format_find_results(query_terms: Sequence[str], matches: Sequence[QueryMatchView]) -> str:
    """Render AND query matches as user-facing text output."""
    parsed_query = _parse_find_query(query_terms)
    query_display = parsed_query.display_query
    lines = [f"Query: {query_display}", f"Matches: {len(matches)}"]

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
