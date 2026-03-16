"""Persistent storage helpers for the inverted index."""

from pathlib import Path
import json
from typing import Any

from src.indexer import InvertedIndex

DEFAULT_INDEX_PATH = Path("data/index.json")


class StorageError(Exception):
    """Raised when index storage operations fail validation or IO."""


def _validate_payload(raw_data: Any) -> dict[str, Any]:
    if not isinstance(raw_data, dict):
        raise StorageError("Index file must contain a JSON object")

    for key in ("meta", "documents", "terms"):
        if key not in raw_data:
            raise StorageError(f"Index file is missing required key: '{key}'")
        if not isinstance(raw_data[key], dict):
            raise StorageError(f"Index key '{key}' must contain an object")

    return raw_data


def save_index(
    index: InvertedIndex,
    *,
    path: str | Path = DEFAULT_INDEX_PATH,
) -> Path:
    """Save an in-memory index to a JSON file and return the file path."""
    target = Path(path)
    if target.exists() and target.is_dir():
        raise StorageError(f"Index path is a directory: {target}")

    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        target.write_text(
            json.dumps(index.to_dict(), indent=2, sort_keys=True),
            encoding="utf-8",
        )
    except OSError as exc:
        raise StorageError(f"Unable to save index file: {target}") from exc

    return target


def load_index(*, path: str | Path = DEFAULT_INDEX_PATH) -> InvertedIndex:
    """Load an index from a JSON file path."""
    source = Path(path)
    if not source.exists():
        raise StorageError(f"Index file not found: {source}")
    if source.is_dir():
        raise StorageError(f"Index path is a directory: {source}")

    try:
        raw_data = json.loads(source.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise StorageError(f"Index file is not valid JSON: {source}") from exc
    except OSError as exc:
        raise StorageError(f"Unable to read index file: {source}") from exc

    raw_data = _validate_payload(raw_data)
    return InvertedIndex.from_dict(raw_data)
