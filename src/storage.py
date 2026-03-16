"""Persistent storage helpers for the inverted index."""

from pathlib import Path
import json

from src.indexer import InvertedIndex

DEFAULT_INDEX_PATH = Path("data/index.json")


def save_index(
    index: InvertedIndex,
    *,
    path: str | Path = DEFAULT_INDEX_PATH,
) -> Path:
    """Save an in-memory index to a JSON file and return the file path."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(index.to_dict(), indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return target
