"""Unit tests for TF-IDF ranking helpers."""

import pytest

from src.indexer import DocumentRecord, create_inverted_index
from src.ranking import (
    apply_proximity_bonus,
    inverse_document_frequency,
    inverse_document_frequency_bm25,
    minimum_position_distance,
    proximity_signal,
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


def test_inverse_document_frequency_bm25_handles_negative_document_frequency() -> None:
    assert inverse_document_frequency_bm25(total_documents=10, document_frequency=-1) == 0.0


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


def test_score_document_bm25_returns_zero_for_missing_document() -> None:
    index = create_inverted_index()
    index.add_document_terms(
        document_id="doc1",
        url="https://quotes.toscrape.com/page/1/",
        tokens=["good"],
    )

    score = score_document_bm25(index, document_id="missing-doc", query_terms=["good"])
    assert score == pytest.approx(0.0)


def test_score_document_bm25_returns_zero_when_average_length_is_zero() -> None:
    index = create_inverted_index()
    index.documents["doc1"] = DocumentRecord(
        url="https://quotes.toscrape.com/page/1/",
        length=0,
    )
    index.meta["page_count"] = 1
    score = score_document_bm25(index, document_id="doc1", query_terms=["good"])
    assert score == pytest.approx(0.0)


def test_score_document_bm25_skips_missing_term_and_missing_posting() -> None:
    index = create_inverted_index()
    index.add_document_terms(
        document_id="doc1",
        url="https://quotes.toscrape.com/page/1/",
        tokens=["truth"],
    )
    index.add_document_terms(
        document_id="doc2",
        url="https://quotes.toscrape.com/page/2/",
        tokens=["good"],
    )

    score = score_document_bm25(
        index,
        document_id="doc1",
        query_terms=["missing", "good"],
    )
    assert score == pytest.approx(0.0)


def test_score_document_bm25_skips_non_positive_denominator() -> None:
    index = create_inverted_index()
    index.add_document_terms(
        document_id="doc1",
        url="https://quotes.toscrape.com/page/1/",
        tokens=["good"],
    )

    score = score_document_bm25(
        index,
        document_id="doc1",
        query_terms=["good"],
        k1=-1.5,
        b=0.0,
    )
    assert score == pytest.approx(0.0)


def test_minimum_position_distance_returns_smallest_gap() -> None:
    distance = minimum_position_distance([10, 1, 5], [7, 3])
    assert distance == 2


def test_minimum_position_distance_returns_none_for_empty_positions() -> None:
    assert minimum_position_distance([], [1, 2]) is None
    assert minimum_position_distance([1, 2], []) is None


def test_minimum_position_distance_stops_on_zero_distance() -> None:
    distance = minimum_position_distance([2, 5], [1, 5, 9])
    assert distance == 0


def test_proximity_signal_prefers_closer_terms() -> None:
    index = create_inverted_index()
    index.add_document_terms(
        document_id="doc-close",
        url="https://quotes.toscrape.com/page/1/",
        tokens=["good", "friends", "truth"],
    )
    index.add_document_terms(
        document_id="doc-far",
        url="https://quotes.toscrape.com/page/2/",
        tokens=["good"] + (["filler"] * 20) + ["friends"],
    )

    signal_close = proximity_signal(
        index,
        document_id="doc-close",
        query_terms=["good", "friends"],
    )
    signal_far = proximity_signal(
        index,
        document_id="doc-far",
        query_terms=["good", "friends"],
    )

    assert signal_close > signal_far
    assert signal_far > 0.0


def test_apply_proximity_bonus_bounds_signal() -> None:
    boosted = apply_proximity_bonus(10.0, proximity=2.0, weight=0.5)
    unchanged_negative = apply_proximity_bonus(10.0, proximity=-1.0, weight=0.5)
    unchanged_zero = apply_proximity_bonus(0.0, proximity=1.0, weight=0.5)

    assert boosted == pytest.approx(15.0)
    assert unchanged_negative == pytest.approx(10.0)
    assert unchanged_zero == pytest.approx(0.0)


def test_proximity_signal_returns_zero_for_single_unique_term() -> None:
    index = create_inverted_index()
    index.add_document_terms(
        document_id="doc1",
        url="https://quotes.toscrape.com/page/1/",
        tokens=["good", "friends"],
    )

    assert proximity_signal(index, document_id="doc1", query_terms=["good", "GOOD"]) == 0.0


def test_proximity_signal_handles_missing_left_and_right_records() -> None:
    index = create_inverted_index()
    index.add_document_terms(
        document_id="doc1",
        url="https://quotes.toscrape.com/page/1/",
        tokens=["good", "friends"],
    )
    index.add_document_terms(
        document_id="doc2",
        url="https://quotes.toscrape.com/page/2/",
        tokens=["rare"],
    )

    missing_left = proximity_signal(
        index,
        document_id="doc1",
        query_terms=["ghost", "good"],
    )
    left_posting_missing = proximity_signal(
        index,
        document_id="doc1",
        query_terms=["rare", "good"],
    )
    missing_right = proximity_signal(
        index,
        document_id="doc1",
        query_terms=["good", "ghost"],
    )
    right_posting_missing = proximity_signal(
        index,
        document_id="doc1",
        query_terms=["good", "rare"],
    )

    assert missing_left == 0.0
    assert left_posting_missing == 0.0
    assert missing_right == 0.0
    assert right_posting_missing == 0.0


def test_proximity_signal_skips_pair_when_distance_is_none() -> None:
    index = create_inverted_index()
    index.add_document_terms(
        document_id="doc1",
        url="https://quotes.toscrape.com/page/1/",
        tokens=["good", "friends"],
    )
    index.terms["friends"].postings["doc1"].positions = []

    assert proximity_signal(index, document_id="doc1", query_terms=["good", "friends"]) == 0.0


def test_apply_proximity_bonus_clamps_negative_weight() -> None:
    score = apply_proximity_bonus(10.0, proximity=1.0, weight=-2.0)
    assert score == pytest.approx(10.0)
