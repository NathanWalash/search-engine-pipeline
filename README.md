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
- CI-based automated test runs

Current collaboration base branch is `feature/project-scaffold`.

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
- `print <word>`
- `find <query>`

### `build`

Build the index by crawling the site and save it to `data/index.json`.

```text
search> build
```

### `load`

Load a previously saved index from `data/index.json`.

```text
search> load
```

### `print <word>`

Display one term entry from the inverted index.

```text
search> print good
```

### `find <query>`

Run case-insensitive AND search across all query terms.

```text
search> find good friends
```

## Testing

Run the full suite:

```bash
python -m pytest
```

Run with concise output:

```bash
python -m pytest -q
```

Coverage reporting is configured in `pytest.ini` and includes:

- terminal coverage summary
- `coverage.xml` output for CI artifacts

## Architecture

The core processing flow is:

```text
crawl -> parse -> index -> store -> search
```

Module responsibilities:

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
    build_pipeline.py
    crawler.py
    indexer.py
    main.py
    parser.py
    search.py
    storage.py
  tests/
    test_build_pipeline.py
    test_cli_shell.py
    test_crawler.py
    test_edge_cases.py
    test_indexer.py
    test_integration_workflow.py
    test_parser.py
    test_scaffold.py
    test_search.py
    test_storage.py
  data/
  docs/
    ROADMAP.md
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
