"""Unit tests for TF-IDF ranking helpers."""

import pytest

from src.indexer import create_inverted_index
from src.ranking import (
    inverse_document_frequency,
    inverse_document_frequency_bm25,
    score_document_bm25,
    score_document_tfidf,
)


def test_inverse_document_frequency_increases_for_rarer_terms() -> None:
    common = inverse_document_frequency(total_documents=10, document_frequency=10)
    rare = inverse_document_frequency(total_documents=10, document_frequency=1)
    assert rare > common


def test_inverse_document_frequency_handles_empty_corpus() -> None:
    assert inverse_document_frequency(total_documents=0, document_frequency=0) == 0.0


def test_inverse_document_frequency_handles_negative_document_frequency() -> None:
    assert inverse_document_frequency(total_documents=10, document_frequency=-1) == 0.0


def test_inverse_document_frequency_bm25_increases_for_rarer_terms() -> None:
    common = inverse_document_frequency_bm25(total_documents=10, document_frequency=10)
    rare = inverse_document_frequency_bm25(total_documents=10, document_frequency=1)
    assert rare > common


def test_inverse_document_frequency_bm25_handles_empty_corpus() -> None:
    assert inverse_document_frequency_bm25(total_documents=0, document_frequency=0) == 0.0


def test_score_document_tfidf_uses_term_frequency_and_idf() -> None:
    index = create_inverted_index()
    index.add_document_terms(
        document_id="doc1",
        url="https://quotes.toscrape.com/page/1/",
        tokens=["good", "good", "truth"],
    )
    index.add_document_terms(
        document_id="doc2",
        url="https://quotes.toscrape.com/page/2/",
        tokens=["good", "friends", "friends", "friends"],
    )

    score_doc1 = score_document_tfidf(
        index,
        document_id="doc1",
        query_terms=["good", "truth"],
    )
    score_doc2 = score_document_tfidf(
        index,
        document_id="doc2",
        query_terms=["good", "truth"],
    )

    assert score_doc1 > score_doc2


def test_score_document_tfidf_returns_zero_for_empty_index() -> None:
    index = create_inverted_index()
    assert (
        score_document_tfidf(index, document_id="doc1", query_terms=["good"]) == 0.0
    )


def test_score_document_tfidf_skips_missing_terms() -> None:
    index = create_inverted_index()
    index.add_document_terms(
        document_id="doc1",
        url="https://quotes.toscrape.com/page/1/",
        tokens=["truth"],
    )

    score = score_document_tfidf(
        index,
        document_id="doc1",
        query_terms=["missing"],
    )

    assert score == pytest.approx(0.0)


def test_score_document_bm25_returns_zero_for_empty_index() -> None:
    index = create_inverted_index()
    assert score_document_bm25(index, document_id="doc1", query_terms=["good"]) == 0.0


def test_score_document_bm25_prefers_shorter_relevant_document() -> None:
    index = create_inverted_index()
    short_tokens = ["good", "friends", "truth"]
    long_tokens = ["good"] * 8 + ["friends"] + ["filler"] * 200
    index.add_document_terms(
        document_id="doc1",
        url="https://quotes.toscrape.com/page/1/",
        tokens=short_tokens,
    )
    index.add_document_terms(
        document_id="doc2",
        url="https://quotes.toscrape.com/page/2/",
        tokens=long_tokens,
    )

    score_doc1 = score_document_bm25(
        index,
        document_id="doc1",
        query_terms=["good", "friends"],
    )
    score_doc2 = score_document_bm25(
        index,
        document_id="doc2",
        query_terms=["good", "friends"],
    )

    assert score_doc1 > score_doc2
