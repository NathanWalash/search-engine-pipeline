# Search Engine Pipeline

Coursework project for building a command-line search engine over `https://quotes.toscrape.com/`.

## Overview

The tool crawls pages from the target website, builds an inverted index, stores the index on disk, and lets you query it from a command-line shell.

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
