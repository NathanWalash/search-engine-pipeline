# COMP3011 Coursework 2 - Advanced Roadmap

This roadmap tracks post-core enhancements.

## Advanced Status Snapshot

Last updated: 2026-03-18

1. Feature A - TF-IDF ranking - complete
2. Feature B - phrase search - complete
3. Feature C - query suggestions - complete
4. Feature D - crawl statistics report - complete
5. Feature E - smarter tokenisation - complete
6. Non-feature hardening pass (CI/testing/code-quality baseline) - complete
7. Feature I - posting-list optimisation for AND queries - complete
8. Feature G - BM25 ranking mode - complete
9. Feature H - proximity-aware ranking bonus - complete
10. Feature F - result snippets with matched-term highlighting - complete
11. Feature J - benchmarking and complexity/performance summary - complete
12. Feature K - incremental reindex performance engine - complete

## Advanced Features Completed

### Feature A - TF-IDF Ranking

- IDF calculation and relevance scoring added
- `find` results ranked by score
- tests confirm ranking order

### Feature B - Phrase Search

- quoted query parsing added
- positional phrase matching implemented
- tests cover exact contiguous phrase behavior

### Feature C - Query Suggestions

- edit-distance suggestion helper added
- `Did you mean` support for missing terms
- tests cover suggestion output paths

### Feature D - Crawl Statistics Report

- crawl metrics collected during build
- build summary output includes crawl/index stats
- tests cover summary generation and integration

### Feature E - Smarter Tokenisation

- internal apostrophes preserved (`don't`, `it's`)
- hyphen strategy is preserve + split (`well-known`, `well`, `known`)
- shared base token position used for canonical/split forms
- tests cover parser and search behaviour for hyphen/apostrophe cases

### Non-Feature Hardening Pass (Completed)

- CI now enforces lint (`ruff`), type checks (`mypy`), and tests with coverage threshold
- publication-quality cleanup baseline applied (docstrings/type-hint consistency pass)
- submission packaging clarified (`data/index.json` remains generated during development)

### Feature I - Posting List Optimisation for Multi-Term AND Queries

- multi-term AND intersections now process terms in ascending document frequency
- query evaluation short-circuits before high-frequency intersections when candidate set is empty
- tests cover ordering and short-circuit behavior equivalence

### Feature G - BM25 Ranking Mode

- BM25 scoring added as an alternative to TF-IDF
- `find` now accepts `--rank tfidf|bm25` (`tfidf` remains the default)
- tests cover ranking-mode selection and BM25 scoring behavior

### Feature H - Proximity-aware Ranking Bonus

- optional bounded proximity bonus added to ranking
- `find` now accepts `--proximity-bonus on|off` (`off` remains default)
- tests cover proximity signal and ranking impact when bonus is enabled

### Feature F - Result Snippets with Matched-Term Highlighting

- optional snippet output added for `find` via `--snippets on|off`
- snippet generation uses deterministic token windows around first match
- matched terms are highlighted in `[]` (including hyphen-aware highlighting)
- document text is now stored in index payload for snippet rendering after load
- tests cover snippet flag parsing, output formatting, and edge boundaries

### Feature J - Benchmarking and Complexity/Performance Summary

- benchmark harness added for reproducible build/reindex, load, and query timings
- query timings include TF-IDF vs BM25, phrase query, and proximity query cases
- `benchmark [--runs N]` CLI command outputs timing report and corpus/index stats
- tests cover benchmark metrics, formatting, and CLI behavior

### Feature K - Incremental Reindex Performance Engine

- `build` now supports `--incremental` mode for reusing unchanged documents
- document `content_hash` tracking added so unchanged pages skip reparse/reindex work
- incremental build summary now reports: reused, reindexed, and new document counts
- benchmark output now includes incremental reuse timing and speedup ratio
- tests cover incremental indexing, CLI flag parsing, and benchmark formatting

## Next Planned Feature Queue

Advanced feature queue complete.

Implementation note: keep features behind small rollout controls while
developing, then switch defaults once validated.

## Final Polish Gate (Non-Lettered)

Status: complete (2026-03-18)

### 1. Professional-grade testing

- strong unit tests across crawler, parser, indexer, search, ranking, and benchmarking paths
- integration tests for build/load/print/find end-to-end behaviour
- mocked crawler tests for deterministic network and failure scenarios
- ranking tests (TF-IDF, BM25, proximity impact)
- phrase, suggestion, and snippet tests
- coverage reporting in CI with stable thresholds
- automated pipeline runs lint, type checks, tests, and coverage on PRs
- final quality snapshot: 186 tests passing, 99.16% total coverage
- benchmark evidence captured in `docs/BENCHMARK_RESULTS.md`

### 2. Publication-quality code

- complete and consistent type hints across modules
- clear docstrings for modules and key helper functions
- clean architecture boundaries (crawl, parse, index, store, search, rank, benchmark)
- small focused functions and minimal duplication
- consistent naming and formatting standards
- modules remain independently testable with deterministic outputs

### 3. README quality

README should read like a polished open-source project and include:

- project overview and architecture
- installation and run instructions
- command usage and examples
- core and advanced feature list
- benchmark/performance summary
- testing instructions and CI notes
- design decisions and tradeoff rationale
- submission workflow and checklist reference
- supporting evidence docs for benchmarking and git workflow traceability

### Polish exit criteria

- all polish sections above are complete,
- codebase is presentation-ready for demo and marking,
- documentation and tests support claims made in the video/report,
- submission checklist prepared in `docs/SUBMISSION_CHECKLIST.md`.

## Suggested Rule for New Advanced Features

For each new feature branch:

1. define one clear goal,
2. implement in small commits,
3. add focused tests,
4. update README/docs,
5. merge only when CI is green.
