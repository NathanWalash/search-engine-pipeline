"""Benchmarking utilities for reproducible build/load/query timings."""

from dataclasses import dataclass
from pathlib import Path
import shutil
import time
from typing import Callable, Optional, Sequence
import uuid

from src.indexer import (
    DocumentRecord,
    InvertedIndex,
    PostingRecord,
    TermRecord,
    TokenPosition,
    create_inverted_index,
)
from src.parser import tokenize_with_positions
from src.search import RankingMode, find_and_match_documents
from src.storage import load_index, save_index


@dataclass(frozen=True)
class QueryBenchmarkCase:
    """One benchmark query scenario."""

    label: str
    query_terms: list[str]
    ranking_mode: RankingMode = "tfidf"
    proximity_bonus: bool = False


@dataclass(frozen=True)
class QueryTiming:
    """Average query timing for one benchmark case."""

    label: str
    average_seconds: float


@dataclass(frozen=True)
class BenchmarkSummary:
    """Aggregated benchmark metrics and corpus stats."""

    runs: int
    build_seconds: float
    incremental_build_seconds: float
    load_seconds: float
    query_timings: list[QueryTiming]
    page_count: int
    unique_terms: int
    token_count: int
    index_size_bytes: int


def _default_query_cases() -> list[QueryBenchmarkCase]:
    """Return benchmark query mix covering ranking and positional query modes."""
    return [
        QueryBenchmarkCase(
            label="tfidf_and",
            query_terms=["good", "friends"],
            ranking_mode="tfidf",
            proximity_bonus=False,
        ),
        QueryBenchmarkCase(
            label="bm25_and",
            query_terms=["good", "friends"],
            ranking_mode="bm25",
            proximity_bonus=False,
        ),
        QueryBenchmarkCase(
            label="phrase_query",
            query_terms=['"good friends"'],
            ranking_mode="tfidf",
            proximity_bonus=False,
        ),
        QueryBenchmarkCase(
            label="proximity_query",
            query_terms=["good", "friends"],
            ranking_mode="tfidf",
            proximity_bonus=True,
        ),
    ]


def _average_seconds(
    task: Callable[[], object],
    *,
    runs: int,
    timer: Callable[[], float],
) -> float:
    """Execute task repeatedly and return mean elapsed seconds."""
    if runs <= 0:
        raise ValueError("runs must be a positive integer")

    total_seconds = 0.0
    for _ in range(runs):
        started_at = timer()
        task()
        total_seconds += timer() - started_at
    return total_seconds / runs


def _token_positions_from_postings(
    index: InvertedIndex,
    *,
    document_id: str,
) -> list[TokenPosition]:
    """Reconstruct token-position pairs from postings when text is unavailable."""
    positions: list[TokenPosition] = []
    for term, term_record in index.terms.items():
        posting = term_record.postings.get(document_id)
        if posting is None:
            continue
        for position in posting.positions:
            positions.append((term, position))

    positions.sort(key=lambda item: (item[1], item[0]))
    return positions


def _rebuild_index(index: InvertedIndex) -> InvertedIndex:
    """Rebuild index content using stored document text or posting fallbacks."""
    rebuilt = create_inverted_index()
    for document_id, document in sorted(index.documents.items()):
        if document.text:
            token_positions = tokenize_with_positions(
                document.text,
                expand_hyphenated=True,
            )
        else:
            token_positions = _token_positions_from_postings(
                index,
                document_id=document_id,
            )

        rebuilt.add_document(
            document_id=document_id,
            url=document.url,
            token_positions=token_positions,
            text=document.text,
        )
    return rebuilt


def _rebuild_index_incremental_reuse(index: InvertedIndex) -> InvertedIndex:
    """Rebuild index by reusing unchanged postings/documents directly."""
    rebuilt = create_inverted_index()
    rebuilt.meta = dict(index.meta)
    rebuilt.documents = {
        document_id: DocumentRecord(
            url=document.url,
            length=document.length,
            text=document.text,
            content_hash=document.content_hash,
        )
        for document_id, document in index.documents.items()
    }
    rebuilt.terms = {
        term: TermRecord(
            document_frequency=term_record.document_frequency,
            postings={
                document_id: PostingRecord(
                    term_frequency=posting.term_frequency,
                    positions=list(posting.positions),
                )
                for document_id, posting in term_record.postings.items()
            },
        )
        for term, term_record in index.terms.items()
    }
    return rebuilt


def _lookup_query_timing(summary: BenchmarkSummary, label: str) -> Optional[float]:
    """Return timing for one label, or None when case is absent."""
    for timing in summary.query_timings:
        if timing.label == label:
            return timing.average_seconds
    return None


def run_benchmark(
    index: InvertedIndex,
    *,
    runs: int = 5,
    query_cases: Optional[Sequence[QueryBenchmarkCase]] = None,
    timer: Callable[[], float] = time.perf_counter,
) -> BenchmarkSummary:
    """Run build/load/query benchmarks for one in-memory index."""
    if runs <= 0:
        raise ValueError("runs must be a positive integer")

    cases = list(query_cases) if query_cases is not None else _default_query_cases()

    build_seconds = _average_seconds(
        lambda: _rebuild_index(index),
        runs=runs,
        timer=timer,
    )
    incremental_build_seconds = _average_seconds(
        lambda: _rebuild_index_incremental_reuse(index),
        runs=runs,
        timer=timer,
    )

    temp_dir = Path(".tmp_benchmarking") / str(uuid.uuid4())
    temp_dir.mkdir(parents=True, exist_ok=False)
    try:
        index_path = temp_dir / "benchmark_index.json"
        save_index(index, path=index_path)
        index_size_bytes = index_path.stat().st_size

        load_seconds = _average_seconds(
            lambda: load_index(path=index_path),
            runs=runs,
            timer=timer,
        )
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

    query_timings: list[QueryTiming] = []
    for case in cases:
        elapsed_seconds = _average_seconds(
            lambda: find_and_match_documents(
                index,
                case.query_terms,
                ranking_mode=case.ranking_mode,
                proximity_bonus=case.proximity_bonus,
            ),
            runs=runs,
            timer=timer,
        )
        query_timings.append(
            QueryTiming(
                label=case.label,
                average_seconds=elapsed_seconds,
            )
        )

    return BenchmarkSummary(
        runs=runs,
        build_seconds=build_seconds,
        incremental_build_seconds=incremental_build_seconds,
        load_seconds=load_seconds,
        query_timings=query_timings,
        page_count=index.meta.get("page_count", len(index.documents)),
        unique_terms=len(index.terms),
        token_count=index.meta.get("token_count", 0),
        index_size_bytes=index_size_bytes,
    )


def format_benchmark_summary(summary: BenchmarkSummary) -> str:
    """Render benchmark metrics as deterministic user-facing text."""
    lines = [
        "Benchmark summary:",
        f"Runs per measurement: {summary.runs}",
        "Timings:",
        f"- Build (reindex): {summary.build_seconds:.6f}s",
        (
            "- Build (incremental reuse): "
            f"{summary.incremental_build_seconds:.6f}s"
        ),
        f"- Load (from JSON): {summary.load_seconds:.6f}s",
        "- Query timings (average):",
    ]

    for timing in summary.query_timings:
        lines.append(f"  - {timing.label}: {timing.average_seconds:.6f}s")

    tfidf_time = _lookup_query_timing(summary, "tfidf_and")
    bm25_time = _lookup_query_timing(summary, "bm25_and")
    if summary.incremental_build_seconds > 0:
        build_speedup = summary.build_seconds / summary.incremental_build_seconds
        lines.append(
            f"Build speedup (full/incremental): {build_speedup:.3f}x"
        )
    if tfidf_time is not None and bm25_time is not None and tfidf_time > 0:
        ratio = bm25_time / tfidf_time
        lines.append(
            f"TF-IDF vs BM25 ratio (bm25/tfidf): {ratio:.3f}x"
        )

    lines.extend(
        [
            "Corpus stats:",
            f"- Pages: {summary.page_count}",
            f"- Unique terms: {summary.unique_terms}",
            f"- Total tokens: {summary.token_count}",
            f"- Index size: {summary.index_size_bytes} bytes",
            "Complexity notes:",
            "- AND intersection uses document-frequency ordering.",
            "- Phrase/proximity query cost depends on positional postings.",
        ]
    )

    return "\n".join(lines)
