"""Tests for print/find command behaviour against indexed data."""

import pytest

import src.main as main_module
from src.indexer import create_inverted_index
from src.main import handle_command
from src.search import find_and_match_documents


def _make_context_with_index() -> main_module.CLIContext:
    index = create_inverted_index()
    index.add_document_terms(
        document_id="doc2",
        url="https://quotes.toscrape.com/page/2/",
        tokens=["good", "friends", "make", "good", "times"],
    )
    index.add_document_terms(
        document_id="doc1",
        url="https://quotes.toscrape.com/page/1/",
        tokens=["truth", "and", "good"],
    )
    return main_module.CLIContext(index=index)


def test_print_existing_term_outputs_index_entry() -> None:
    context = _make_context_with_index()
    message, should_exit = handle_command("print good", context=context)

    assert should_exit is False
    assert "Word: good" in message
    assert "Document frequency: 2" in message
    assert "https://quotes.toscrape.com/page/1/" in message
    assert "https://quotes.toscrape.com/page/2/" in message


def test_print_missing_term_reports_not_found() -> None:
    context = _make_context_with_index()
    message, should_exit = handle_command("print banana", context=context)

    assert should_exit is False
    assert message == "Word not found in index"


def test_find_single_word_returns_matching_pages() -> None:
    context = _make_context_with_index()
    message, should_exit = handle_command("find truth", context=context)

    assert should_exit is False
    assert "Query: truth" in message
    assert "Matches: 1" in message
    assert "https://quotes.toscrape.com/page/1/" in message


def test_find_multi_word_uses_and_semantics() -> None:
    context = _make_context_with_index()
    message, should_exit = handle_command("find good friends", context=context)

    assert should_exit is False
    assert "Query: good friends" in message
    assert "Matches: 1" in message
    assert "https://quotes.toscrape.com/page/2/" in message
    assert "https://quotes.toscrape.com/page/1/" not in message


def test_find_is_case_insensitive() -> None:
    context = _make_context_with_index()
    message, should_exit = handle_command("find GOOD", context=context)

    assert should_exit is False
    assert "Query: good" in message
    assert "Matches: 2" in message


def test_find_normalises_duplicate_terms() -> None:
    context = _make_context_with_index()
    message, should_exit = handle_command("find GOOD good", context=context)

    assert should_exit is False
    assert "Query: good" in message
    assert "Matches: 2" in message


def test_print_requires_loaded_index_in_context() -> None:
    context = main_module.CLIContext(index=None)

    with pytest.raises(ValueError, match="no index loaded"):
        handle_command("print good", context=context)


def test_find_and_match_documents_empty_query_returns_empty() -> None:
    index = create_inverted_index()
    assert find_and_match_documents(index, []) == []


def test_find_and_match_documents_missing_term_returns_empty() -> None:
    index = create_inverted_index()
    index.add_document_terms(
        document_id="doc1",
        url="https://quotes.toscrape.com/page/1/",
        tokens=["truth"],
    )
    assert find_and_match_documents(index, ["missing"]) == []


def test_find_and_match_documents_skips_missing_document_metadata() -> None:
    index = create_inverted_index()
    index.add_document_terms(
        document_id="doc1",
        url="https://quotes.toscrape.com/page/1/",
        tokens=["truth"],
    )
    del index.documents["doc1"]

    assert find_and_match_documents(index, ["truth"]) == []
