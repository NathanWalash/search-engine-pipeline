# Search Engine Pipeline

Coursework project for building a command-line search engine over `https://quotes.toscrape.com/`.

## Overview

The tool crawls pages from the target website, builds an inverted index, stores the index on disk, and lets you query it from a command-line shell.

## Status

Core roadmap phases (1-10) are implemented, including:

- crawl/build pipeline
- index save/load
- `print` and `find` query commands
- integration and edge-case tests
- CI checks for lint, type-checking, and coverage-gated tests

Implemented advanced features:

- TF-IDF result ranking
- BM25 ranking mode (`find --rank bm25`)
- proximity-aware ranking bonus (`find --proximity-bonus on`)
- result snippets with matched-term highlighting (`find --snippets on`)
- benchmarking summary (`benchmark --runs N`)
- quoted phrase search
- query suggestions (`Did you mean`)
- crawl statistics reporting
- smarter tokenisation for apostrophes and hyphenated words
- posting-list optimisation for multi-term AND queries

Roadmap planning docs are split into:

- `docs/CORE_ROADMAP.md`
- `docs/ADVANCED_ROADMAP.md`

## Installation

### Prerequisites

- Python 3.11 or 3.12
- pip

### Setup

```bash
python -m pip install -r requirements.txt
```

## Running the CLI

```bash
python -m src.main
```

You will see the interactive prompt:

```text
search>
```

## Command Usage

- `build`
- `load`
- `benchmark [--runs N]`
- `print <word>`
- `find [--rank tfidf|bm25] [--proximity-bonus on|off] [--snippets on|off] <query>`

### `build`

Build the index by crawling the site and save it to `data/index.json`.

```text
search> build
```

By default, the crawler enforces a 6-second politeness delay between requests.
For local testing only, you can override this before starting the CLI:

```powershell
$env:SEARCH_POLITENESS_SECONDS = "1.0"
python -m src.main
```

The `build` output includes live crawl progress lines:

```text
Build: crawled N page(s) (last: <url>)
```

After crawl/indexing, `build` also prints a crawl report summary:

- pages crawled / failed
- URLs discovered / visited
- crawl success rate
- unique terms, token count, and duration

### `load`

Load a previously saved index from `data/index.json`.

```text
search> load
```

Submission note: `data/index.json` is treated as a generated artifact and is
git-ignored during development. For final submission, generate a fresh index
and include the compiled index file as required by the coursework brief.

### `print <word>`

Display one term entry from the inverted index.

```text
search> print good
```

### `benchmark [--runs N]`

Run performance measurements for:

- build/reindex timing
- load timing
- query timings (TF-IDF, BM25, phrase, proximity)
- corpus and index-size stats

```text
search> benchmark
search> benchmark --runs 10
```

### `find <query>`

Run case-insensitive AND search across all query terms.
Matched documents are ranked by TF-IDF by default, or BM25 with `--rank bm25`.
Optional proximity bonus (`--proximity-bonus on`) boosts documents where
query terms occur close together.
Optional snippets (`--snippets on`) include a short context window with
matched terms highlighted in `[]`.
Quoted phrases are supported using positional matching.
Misspelled terms can return a `Did you mean` suggestion.
Multi-term AND intersections are optimized by processing rarer terms first.

```text
search> find good friends
search> find --rank bm25 good friends
search> find --proximity-bonus on good friends
search> find --snippets on good friends
search> find "good friends"
search> find well-known
search> find well known
```

## Tokenisation Rules

Index tokenisation currently applies these rules:

- lowercase all text
- preserve apostrophes inside words (`don't`, `it's`)
- preserve canonical hyphenated terms (`well-known`)
- also index split parts of hyphenated terms (`well`, `known`)
- strip leading/trailing punctuation
- ignore empty tokens

Hyphen strategy is `preserve + split`, so queries like `well-known`,
`well known`, and `known` can all match hyphenated content.

## Testing

Run the full suite:

```bash
python -m pytest
```

Run with concise output:

```bash
python -m pytest -q
```

Run lint checks:

```bash
python -m ruff check src tests
```

Run static type checks:

```bash
python -m mypy src
```

Coverage reporting is configured in `pytest.ini` and includes:

- terminal coverage summary
- `coverage.xml` output for CI artifacts
- minimum coverage threshold (`--cov-fail-under=95`)

## Architecture

The core processing flow is:

```text
crawl -> parse -> index -> store -> search
```

Module responsibilities:

- `src/benchmarking.py`: benchmark harness and report formatting
- `src/crawler.py`: HTTP fetching, politeness delay, internal-link BFS crawl
- `src/parser.py`: HTML text extraction, tokenization, token positions
- `src/indexer.py`: inverted index data model and document/term statistics
- `src/build_pipeline.py`: crawl+parse+index orchestration
- `src/storage.py`: JSON save/load with validation
- `src/search.py`: `print`/`find` query logic and output formatting
- `src/main.py`: interactive CLI command dispatch

## Project Layout

```text
search-engine-pipeline/
  src/
    benchmarking.py
    build_pipeline.py
    crawler.py
    indexer.py
    main.py
    parser.py
    ranking.py
    search.py
    storage.py
  tests/
    test_benchmarking.py
    test_build_pipeline.py
    test_cli_shell.py
    test_crawler.py
    test_edge_cases.py
    test_indexer.py
    test_integration_workflow.py
    test_parser.py
    test_ranking.py
    test_scaffold.py
    test_search.py
    test_storage.py
  data/
  docs/
    ROADMAP.md
    CORE_ROADMAP.md
    ADVANCED_ROADMAP.md
    SPECIFICATION.md
  .github/workflows/ci.yml
  README.md
  requirements.txt
```

## Demo Checklist

Use this as a pre-recording checklist for the 5-minute demo.

- Show `build` running and confirm index save path
- Show `load` running against the saved index file
- Show `print <word>` for:
  - an existing term
  - a missing term
- Show `find <query>` for:
  - a single term query
  - a multi-term AND query
- Show an edge case:
  - empty `find`
  - missing index file for `load`
- Show `benchmark` output (`benchmark --runs 3`)
- Run the test suite in terminal (`python -m pytest -q`)
- Show commit history for incremental branch-based development

## GenAI Usage Notes (Scaffold)

Fill this before recording so the reflection section stays specific and concise.

```text
GenAI tools used:
- Tool:
- Purpose:

Example where GenAI helped:
- Task:
- Suggested output:
- What I kept:
- What I changed and why:

Example where GenAI hindered or was incorrect:
- Task:
- Problem in output:
- How I detected it:
- Fix I applied:

Impact on learning and workflow:
- Time saved:
- Concepts learned:
- Debugging effort:
- What I would do differently next time:
```
