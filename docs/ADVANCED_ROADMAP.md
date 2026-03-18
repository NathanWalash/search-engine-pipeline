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

## Next Planned Feature Queue (J)

Implementation note: keep features behind small rollout controls while
developing, then switch defaults once validated.

### Feature J - Benchmarking and complexity/performance summary

#### Goal

Provide reproducible performance/complexity evidence for build, load, and
query operations.

#### Suggested branch

`feature/benchmarking-summary`

#### Suggested commits

1. `feat: add benchmark harness for build load and query timings`
2. `feat: report tf-idf vs bm25 and phrase/proximity query timings`
3. `feat: include index size and corpus stats in benchmark summary`
4. `docs: add performance report template and interpretation notes`

#### Exit criteria

- benchmark commands are reproducible and documented,
- timing reports include build/load/query comparisons,
- index-size and corpus statistics are captured in summary output.

## Recommended implementation order

1. Feature J (final performance and complexity evidence)

## Final Polish Gate (Non-Lettered)

This is required before final submission and sits across all advanced work.

### 1. Professional-grade testing

- strong unit tests across crawler, parser, indexer, search, and ranking paths
- integration tests for build/load/print/find end-to-end behaviour
- mocked crawler tests for deterministic network and failure scenarios
- ranking tests (TF-IDF, BM25, proximity impact)
- phrase and suggestion tests
- coverage reporting in CI with stable thresholds
- automated pipeline that runs lint, tests, and coverage on PRs

### 2. Publication-quality code

- complete and consistent type hints
- clear docstrings for modules and non-trivial functions
- clean architecture boundaries (crawl, parse, index, store, search, rank)
- small focused functions and minimal duplication
- consistent naming and formatting standards
- avoid hidden coupling and keep modules independently testable

### 3. README quality

README should read like a polished open-source project and include:

- project overview and architecture
- installation and run instructions
- command usage and examples
- core and advanced feature list
- benchmark/performance summary
- testing instructions and CI notes
- design decisions and tradeoff rationale

### Polish exit criteria

- all polish sections above are demonstrably complete,
- codebase is presentation-ready for demo and marking,
- documentation and tests support claims made in the video/report.

## Suggested Rule for New Advanced Features

For each new feature branch:

1. define one clear goal,
2. implement in small commits,
3. add focused tests,
4. update README/docs,
5. merge only when CI is green.
