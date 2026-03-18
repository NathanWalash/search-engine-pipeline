"""Tests for print/find command behaviour against indexed data."""

import pytest

import src.main as main_module
import src.search as search_module
from src.indexer import create_inverted_index
from src.main import handle_command
from src.parser import parse_html
from src.search import (
    find_and_match_documents,
    suggest_closest_term,
    suggest_query_terms,
)


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


def test_find_and_match_documents_ranks_by_tfidf_score() -> None:
    index = create_inverted_index()
    index.add_document_terms(
        document_id="doc1",
        url="https://quotes.toscrape.com/page/1/",
        tokens=["good", "friends"],
    )
    index.add_document_terms(
        document_id="doc2",
        url="https://quotes.toscrape.com/page/2/",
        tokens=["good", "good", "good", "friends"],
    )

    matches = find_and_match_documents(index, ["good", "friends"])

    assert [match.document_id for match in matches] == ["doc2", "doc1"]
    assert matches[0].relevance_score > matches[1].relevance_score


def test_find_and_match_documents_tie_breaks_by_url_then_document_id() -> None:
    index = create_inverted_index()
    index.add_document_terms(
        document_id="doc2",
        url="https://quotes.toscrape.com/page/2/",
        tokens=["good"],
    )
    index.add_document_terms(
        document_id="doc1",
        url="https://quotes.toscrape.com/page/1/",
        tokens=["good"],
    )

    matches = find_and_match_documents(index, ["good"])

    assert [match.document_id for match in matches] == ["doc1", "doc2"]


def test_find_output_includes_tfidf_score() -> None:
    context = _make_context_with_index()
    message, should_exit = handle_command("find good", context=context)

    assert should_exit is False
    assert "score=" in message


def test_find_output_supports_bm25_ranking_flag() -> None:
    context = _make_context_with_index()
    message, should_exit = handle_command("find --rank bm25 good", context=context)

    assert should_exit is False
    assert "Query: good" in message
    assert "Matches: 2" in message
    assert "score=" in message


def test_find_phrase_query_matches_exact_order_only() -> None:
    index = create_inverted_index()
    index.add_document_terms(
        document_id="doc1",
        url="https://quotes.toscrape.com/page/1/",
        tokens=["good", "friends", "forever"],
    )
    index.add_document_terms(
        document_id="doc2",
        url="https://quotes.toscrape.com/page/2/",
        tokens=["friends", "good", "forever"],
    )
    context = main_module.CLIContext(index=index)

    message, should_exit = handle_command('find "good friends"', context=context)

    assert should_exit is False
    assert 'Query: "good friends"' in message
    assert "Matches: 1" in message
    assert "https://quotes.toscrape.com/page/1/" in message
    assert "https://quotes.toscrape.com/page/2/" not in message


def test_find_phrase_query_combines_with_term_filter() -> None:
    index = create_inverted_index()
    index.add_document_terms(
        document_id="doc1",
        url="https://quotes.toscrape.com/page/1/",
        tokens=["good", "friends", "truth"],
    )
    index.add_document_terms(
        document_id="doc2",
        url="https://quotes.toscrape.com/page/2/",
        tokens=["good", "friends"],
    )
    context = main_module.CLIContext(index=index)

    message, should_exit = handle_command(
        'find "good friends" truth',
        context=context,
    )

    assert should_exit is False
    assert "Matches: 1" in message
    assert "https://quotes.toscrape.com/page/1/" in message
    assert "https://quotes.toscrape.com/page/2/" not in message


def test_find_phrase_query_returns_no_matches_for_non_contiguous_terms() -> None:
    index = create_inverted_index()
    index.add_document_terms(
        document_id="doc1",
        url="https://quotes.toscrape.com/page/1/",
        tokens=["good", "kind", "friends"],
    )
    context = main_module.CLIContext(index=index)

    message, should_exit = handle_command('find "good friends"', context=context)

    assert should_exit is False
    assert message == "No matching pages found."


def test_suggest_closest_term_returns_nearest_indexed_word() -> None:
    index = create_inverted_index()
    index.add_document_terms(
        document_id="doc1",
        url="https://quotes.toscrape.com/page/1/",
        tokens=["friend", "truth"],
    )

    assert suggest_closest_term(index, "frend") == "friend"


def test_suggest_closest_term_returns_none_for_far_terms() -> None:
    index = create_inverted_index()
    index.add_document_terms(
        document_id="doc1",
        url="https://quotes.toscrape.com/page/1/",
        tokens=["friend", "truth"],
    )

    assert suggest_closest_term(index, "zzzzzz") is None


def test_suggest_query_terms_includes_phrase_tokens() -> None:
    index = create_inverted_index()
    index.add_document_terms(
        document_id="doc1",
        url="https://quotes.toscrape.com/page/1/",
        tokens=["good", "friends"],
    )

    suggestions = suggest_query_terms(index, ['"godo friends"'])

    assert suggestions == {"godo": "good"}


def test_hyphenated_indexing_supports_exact_and_split_queries() -> None:
    index = create_inverted_index()
    parsed_hyphenated = parse_html("<p>well-known author</p>")
    parsed_split = parse_html("<p>well known writer</p>")
    index.add_document(
        document_id="doc1",
        url="https://quotes.toscrape.com/page/1/",
        token_positions=parsed_hyphenated.token_positions,
    )
    index.add_document(
        document_id="doc2",
        url="https://quotes.toscrape.com/page/2/",
        token_positions=parsed_split.token_positions,
    )
    context = main_module.CLIContext(index=index)

    exact_message, _ = handle_command("find well-known", context=context)
    split_message, _ = handle_command("find well known", context=context)
    single_message, _ = handle_command("find known", context=context)

    assert "Matches: 1" in exact_message
    assert "https://quotes.toscrape.com/page/1/" in exact_message
    assert "https://quotes.toscrape.com/page/2/" not in exact_message

    assert "Matches: 2" in split_message
    assert "https://quotes.toscrape.com/page/1/" in split_message
    assert "https://quotes.toscrape.com/page/2/" in split_message

    assert "Matches: 2" in single_message
    assert "https://quotes.toscrape.com/page/1/" in single_message
    assert "https://quotes.toscrape.com/page/2/" in single_message


def test_find_orders_term_intersection_by_document_frequency(monkeypatch) -> None:
    index = create_inverted_index()
    index.add_document_terms(
        document_id="doc1",
        url="https://quotes.toscrape.com/page/1/",
        tokens=["common", "rare", "medium"],
    )
    index.add_document_terms(
        document_id="doc2",
        url="https://quotes.toscrape.com/page/2/",
        tokens=["common", "medium"],
    )
    index.add_document_terms(
        document_id="doc3",
        url="https://quotes.toscrape.com/page/3/",
        tokens=["common"],
    )

    captured: dict[str, list[str]] = {}
    original_intersector = search_module._intersect_term_document_ids

    def spy_intersector(term_records, ordered_terms):
        captured["ordered_terms"] = list(ordered_terms)
        return original_intersector(term_records, ordered_terms)

    monkeypatch.setattr(
        search_module,
        "_intersect_term_document_ids",
        spy_intersector,
    )

    matches = find_and_match_documents(index, ["common", "rare", "medium"])

    assert captured["ordered_terms"] == ["rare", "medium", "common"]
    assert [match.document_id for match in matches] == ["doc1"]


class _TrackingPostings(dict[str, object]):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.iter_calls = 0

    def __iter__(self):  # type: ignore[override]
        self.iter_calls += 1
        return super().__iter__()


def test_find_short_circuits_before_high_df_term_intersection() -> None:
    index = create_inverted_index()
    index.add_document_terms(
        document_id="doc1",
        url="https://quotes.toscrape.com/page/1/",
        tokens=["common", "rare-a"],
    )
    index.add_document_terms(
        document_id="doc2",
        url="https://quotes.toscrape.com/page/2/",
        tokens=["common", "rare-b"],
    )
    index.add_document_terms(
        document_id="doc3",
        url="https://quotes.toscrape.com/page/3/",
        tokens=["common"],
    )

    common_tracking = _TrackingPostings(index.terms["common"].postings)
    index.terms["common"].postings = common_tracking  # type: ignore[assignment]

    matches = find_and_match_documents(index, ["common", "rare-a", "rare-b"])

    assert matches == []
    assert common_tracking.iter_calls == 0


def test_find_ranking_mode_switches_between_tfidf_and_bm25(monkeypatch) -> None:
    index = create_inverted_index()
    index.add_document_terms(
        document_id="doc1",
        url="https://quotes.toscrape.com/page/1/",
        tokens=["good"],
    )
    index.add_document_terms(
        document_id="doc2",
        url="https://quotes.toscrape.com/page/2/",
        tokens=["good"],
    )

    def fake_tfidf(index, *, document_id: str, query_terms) -> float:
        del index, query_terms
        return 10.0 if document_id == "doc1" else 1.0

    def fake_bm25(index, *, document_id: str, query_terms, k1=1.5, b=0.75) -> float:
        del index, query_terms, k1, b
        return 10.0 if document_id == "doc2" else 1.0

    monkeypatch.setattr(search_module, "score_document_tfidf", fake_tfidf)
    monkeypatch.setattr(search_module, "score_document_bm25", fake_bm25)

    tfidf_matches = find_and_match_documents(index, ["good"], ranking_mode="tfidf")
    bm25_matches = find_and_match_documents(index, ["good"], ranking_mode="bm25")

    assert [match.document_id for match in tfidf_matches] == ["doc1", "doc2"]
    assert [match.document_id for match in bm25_matches] == ["doc2", "doc1"]


def test_find_rejects_unsupported_ranking_mode() -> None:
    index = create_inverted_index()
    index.add_document_terms(
        document_id="doc1",
        url="https://quotes.toscrape.com/page/1/",
        tokens=["good"],
    )

    with pytest.raises(ValueError, match="Unsupported ranking mode"):
        find_and_match_documents(index, ["good"], ranking_mode="bad-mode")  # type: ignore[arg-type]
