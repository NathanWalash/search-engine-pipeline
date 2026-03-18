"""Unit tests for benchmarking helpers."""

import pytest

from src.benchmarking import (
    format_benchmark_summary,
    run_benchmark,
)
from src.indexer import InvertedIndex, create_inverted_index


class _FakeTimer:
    def __init__(self, step: float = 0.01) -> None:
        self._value = 0.0
        self._step = step

    def __call__(self) -> float:
        current = self._value
        self._value += self._step
        return current


def _make_index(*, include_text: bool) -> InvertedIndex:
    index = create_inverted_index()
    index.add_document_terms(
        document_id="doc1",
        url="https://quotes.toscrape.com/page/1/",
        tokens=["good", "friends", "truth"],
        text="Good friends and truth." if include_text else "",
    )
    index.add_document_terms(
        document_id="doc2",
        url="https://quotes.toscrape.com/page/2/",
        tokens=["good", "kind", "people"],
        text="Good and kind people." if include_text else "",
    )
    return index


def test_run_benchmark_returns_expected_metrics_with_text() -> None:
    index = _make_index(include_text=True)
    summary = run_benchmark(index, runs=2, timer=_FakeTimer())

    labels = {timing.label for timing in summary.query_timings}
    assert labels == {
        "tfidf_and",
        "bm25_and",
        "phrase_query",
        "proximity_query",
    }
    assert summary.page_count == 2
    assert summary.unique_terms > 0
    assert summary.token_count > 0
    assert summary.index_size_bytes > 0
    assert summary.build_seconds > 0
    assert summary.load_seconds > 0


def test_run_benchmark_supports_posting_rebuild_when_text_missing() -> None:
    index = _make_index(include_text=False)
    summary = run_benchmark(index, runs=1, timer=_FakeTimer())

    assert summary.page_count == 2
    assert summary.unique_terms > 0
    assert summary.token_count > 0


def test_run_benchmark_rejects_non_positive_runs() -> None:
    index = _make_index(include_text=True)
    with pytest.raises(ValueError, match="runs must be a positive integer"):
        run_benchmark(index, runs=0)


def test_format_benchmark_summary_includes_key_sections() -> None:
    index = _make_index(include_text=True)
    summary = run_benchmark(index, runs=1, timer=_FakeTimer())
    rendered = format_benchmark_summary(summary)

    assert "Benchmark summary:" in rendered
    assert "Build (reindex):" in rendered
    assert "Load (from JSON):" in rendered
    assert "phrase_query" in rendered
    assert "proximity_query" in rendered
    assert "TF-IDF vs BM25 ratio" in rendered
    assert "Corpus stats:" in rendered
