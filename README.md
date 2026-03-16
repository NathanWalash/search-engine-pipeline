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

## Project Layout

- `src/` application modules
- `tests/` test suite
- `data/` generated index artifacts
- `docs/` project specification and roadmap
