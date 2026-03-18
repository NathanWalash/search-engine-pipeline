# Benchmark Results

This document records reproducible benchmark evidence for submission.

## Run Metadata

- date: 2026-03-18
- command path: `python -m src.main`
- benchmark command: `benchmark --runs 5`
- index source: `data/index.json`
- corpus snapshot:
  - pages: 214
  - unique terms: 4570
  - total tokens: 37576

## Quality Gate Snapshot

Executed immediately before benchmarking:

- `python -m ruff check src tests` -> pass
- `python -m mypy src` -> pass
- `python -m pytest -q` -> pass
- tests passing: 179
- total coverage: 99.37%

## Benchmark Output (Runs = 5)

```text
Benchmark summary:
Runs per measurement: 5
Timings:
- Build (reindex): 0.487496s
- Load (from JSON): 0.308592s
- Query timings (average):
  - tfidf_and: 0.000531s
  - bm25_and: 0.001532s
  - phrase_query: 0.000322s
  - proximity_query: 0.000743s
TF-IDF vs BM25 ratio (bm25/tfidf): 2.883x
Corpus stats:
- Pages: 214
- Unique terms: 4570
- Total tokens: 37576
- Index size: 3339951 bytes
Complexity notes:
- AND intersection uses document-frequency ordering.
- Phrase/proximity query cost depends on positional postings.
```

## Re-run Instructions

```bash
python -m src.main
# then in shell:
load
benchmark --runs 5
```

For more stable timing statistics, increase runs to 10 or 20.
