"""Tests for print/find command behaviour against indexed data."""

import src.main as main_module
from src.indexer import create_inverted_index
from src.main import handle_command


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
