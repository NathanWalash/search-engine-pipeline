"""Ranking helpers for query result ordering."""

from math import log
from typing import Sequence

from src.indexer import InvertedIndex

# 0.35 caps the bonus at a 35% score uplift, keeping proximity as a tiebreaker
# rather than overriding term-frequency relevance for strongly matching documents.
PROXIMITY_BONUS_WEIGHT = 0.35


def inverse_document_frequency(
    *,
    total_documents: int,
    document_frequency: int,
) -> float:
    """Return a smoothed IDF weight for one term."""
    if total_documents <= 0:
        return 0.0
    if document_frequency < 0:
        return 0.0
    # +1 additive smoothing prevents zero IDF for terms that appear in every document,
    # and the trailing +1 keeps the weight positive for common terms.
    return log((total_documents + 1) / (document_frequency + 1)) + 1.0


def score_document_tfidf(
    index: InvertedIndex,
    *,
    document_id: str,
    query_terms: Sequence[str],
) -> float:
    """Return a TF-IDF style score for one matched document."""
    total_documents = max(index.meta.get("page_count", 0), len(index.documents))
    if total_documents <= 0:
        return 0.0

    score = 0.0
    for term in query_terms:
        term_record = index.terms.get(term)
        if term_record is None:
            continue

        posting = term_record.postings.get(document_id)
        if posting is None:
            continue

        idf = inverse_document_frequency(
            total_documents=total_documents,
            document_frequency=term_record.document_frequency,
        )
        score += posting.term_frequency * idf

    return score


def inverse_document_frequency_bm25(
    *,
    total_documents: int,
    document_frequency: int,
) -> float:
    """Return BM25 IDF weight for one term."""
    if total_documents <= 0:
        return 0.0
    if document_frequency < 0:
        return 0.0
    return log(
        1.0 + ((total_documents - document_frequency + 0.5) / (document_frequency + 0.5))
    )


def score_document_bm25(
    index: InvertedIndex,
    *,
    document_id: str,
    query_terms: Sequence[str],
    k1: float = 1.5,   # controls term-frequency saturation; standard literature default
    b: float = 0.75,   # controls document-length normalisation; standard literature default
) -> float:
    """Return BM25 score for one matched document."""
    total_documents = max(index.meta.get("page_count", 0), len(index.documents))
    if total_documents <= 0:
        return 0.0

    document = index.documents.get(document_id)
    if document is None:
        return 0.0

    total_length = sum(record.length for record in index.documents.values())
    average_document_length = total_length / len(index.documents) if index.documents else 0.0
    if average_document_length <= 0:
        return 0.0

    score = 0.0
    document_length = document.length
    for term in query_terms:
        term_record = index.terms.get(term)
        if term_record is None:
            continue

        posting = term_record.postings.get(document_id)
        if posting is None:
            continue

        idf = inverse_document_frequency_bm25(
            total_documents=total_documents,
            document_frequency=term_record.document_frequency,
        )
        tf = posting.term_frequency
        # BM25 length normalisation: b=1 fully normalises by doc length, b=0 ignores it.
        normalization = k1 * (1.0 - b + b * (document_length / average_document_length))
        denominator = tf + normalization
        if denominator <= 0:
            continue

        score += idf * ((tf * (k1 + 1.0)) / denominator)

    return score


def minimum_position_distance(
    left_positions: Sequence[int],
    right_positions: Sequence[int],
) -> int | None:
    """Return the smallest absolute distance between two sorted/unsorted lists."""
    if not left_positions or not right_positions:
        return None

    left_sorted = sorted(left_positions)
    right_sorted = sorted(right_positions)
    left_index = 0
    right_index = 0
    best: int | None = None

    while left_index < len(left_sorted) and right_index < len(right_sorted):
        left_value = left_sorted[left_index]
        right_value = right_sorted[right_index]
        distance = abs(left_value - right_value)
        if best is None or distance < best:
            best = distance
            if best == 0:
                break

        if left_value <= right_value:
            left_index += 1
            continue
        right_index += 1

    return best


def proximity_signal(
    index: InvertedIndex,
    *,
    document_id: str,
    query_terms: Sequence[str],
) -> float:
    """Return [0, 1] signal where larger means query terms occur closer together."""
    unique_terms: list[str] = []
    seen_terms: set[str] = set()
    for term in query_terms:
        lowered = term.lower()
        if lowered in seen_terms:
            continue
        seen_terms.add(lowered)
        unique_terms.append(lowered)

    if len(unique_terms) < 2:
        return 0.0

    pair_scores: list[float] = []
    for index_left, left_term in enumerate(unique_terms):
        left_record = index.terms.get(left_term)
        if left_record is None:
            continue
        left_posting = left_record.postings.get(document_id)
        if left_posting is None:
            continue

        for right_term in unique_terms[index_left + 1 :]:
            right_record = index.terms.get(right_term)
            if right_record is None:
                continue
            right_posting = right_record.postings.get(document_id)
            if right_posting is None:
                continue

            distance = minimum_position_distance(
                left_posting.positions,
                right_posting.positions,
            )
            if distance is None:
                continue

            # 1/(1+d): distance 0 → score 1.0, decays toward 0 as terms move apart.
            pair_scores.append(1.0 / (1.0 + distance))

    if not pair_scores:
        return 0.0
    return sum(pair_scores) / len(pair_scores)


def apply_proximity_bonus(
    base_score: float,
    *,
    proximity: float,
    weight: float = PROXIMITY_BONUS_WEIGHT,
) -> float:
    """Apply bounded proximity bonus to a base relevance score."""
    if base_score <= 0:
        return base_score

    bounded_proximity = min(1.0, max(0.0, proximity))
    bounded_weight = max(0.0, weight)
    return base_score * (1.0 + (bounded_weight * bounded_proximity))
