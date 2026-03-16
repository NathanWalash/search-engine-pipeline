"""Ranking helpers for query result ordering."""

from math import log
from typing import Sequence

from src.indexer import InvertedIndex


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
