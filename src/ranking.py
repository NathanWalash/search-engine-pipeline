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
    k1: float = 1.5,
    b: float = 0.75,
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
        normalization = k1 * (1.0 - b + b * (document_length / average_document_length))
        denominator = tf + normalization
        if denominator <= 0:
            continue

        score += idf * ((tf * (k1 + 1.0)) / denominator)

    return score
