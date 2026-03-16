"""Unit tests for inverted index update behaviour."""

import pytest

from src.indexer import create_inverted_index


def test_first_occurrence_creates_term_posting() -> None:
    index = create_inverted_index()
    index.add_document(
        document_id="doc1",
        url="https://quotes.toscrape.com/page/1/",
        token_positions=[("friend", 0)],
    )

    friend = index.terms["friend"]
    assert friend.document_frequency == 1
    assert friend.postings["doc1"].term_frequency == 1
    assert friend.postings["doc1"].positions == [0]


def test_repeated_term_in_one_document_tracks_tf_and_positions() -> None:
    index = create_inverted_index()
    index.add_document(
        document_id="doc1",
        url="https://quotes.toscrape.com/page/1/",
        token_positions=[("truth", 1), ("truth", 4), ("truth", 10)],
    )

    posting = index.terms["truth"].postings["doc1"]
    assert posting.term_frequency == 3
    assert posting.positions == [1, 4, 10]


def test_same_term_across_documents_updates_document_frequency() -> None:
    index = create_inverted_index()
    index.add_document(
        document_id="doc1",
        url="https://quotes.toscrape.com/page/1/",
        token_positions=[("good", 0), ("friends", 1)],
    )
    index.add_document(
        document_id="doc2",
        url="https://quotes.toscrape.com/page/2/",
        token_positions=[("good", 2)],
    )

    assert index.terms["good"].document_frequency == 2
    assert set(index.terms["good"].postings.keys()) == {"doc1", "doc2"}


def test_meta_and_document_statistics_are_updated() -> None:
    index = create_inverted_index()
    index.add_document(
        document_id="doc1",
        url="https://quotes.toscrape.com/page/1/",
        token_positions=[("alpha", 0), ("beta", 1), ("alpha", 2)],
    )

    assert index.meta["page_count"] == 1
    assert index.meta["token_count"] == 3
    assert index.documents["doc1"].url == "https://quotes.toscrape.com/page/1/"
    assert index.documents["doc1"].length == 3


def test_add_document_terms_infers_positions() -> None:
    index = create_inverted_index()
    index.add_document_terms(
        document_id="doc1",
        url="https://quotes.toscrape.com/page/1/",
        tokens=["one", "two", "one"],
    )

    posting = index.terms["one"].postings["doc1"]
    assert posting.term_frequency == 2
    assert posting.positions == [0, 2]


def test_duplicate_document_id_raises_error() -> None:
    index = create_inverted_index()
    index.add_document(
        document_id="doc1",
        url="https://quotes.toscrape.com/page/1/",
        token_positions=[("x", 0)],
    )

    with pytest.raises(ValueError, match="already indexed"):
        index.add_document(
            document_id="doc1",
            url="https://quotes.toscrape.com/page/2/",
            token_positions=[("y", 0)],
        )
