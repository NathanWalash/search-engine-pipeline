"""Persistent storage helpers for the inverted index."""

from pathlib import Path
import json
from typing import Any

from src.indexer import InvertedIndex

DEFAULT_INDEX_PATH = Path("data/index.json")


class StorageError(Exception):
    """Raised when index storage operations fail validation or IO."""


def _require_int(value: Any, *, field_name: str) -> int:
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise StorageError(f"Index field '{field_name}' must be an integer") from exc


def _validate_payload(raw_data: Any) -> dict[str, Any]:
    if not isinstance(raw_data, dict):
        raise StorageError("Index file must contain a JSON object")

    for key in ("meta", "documents", "terms"):
        if key not in raw_data:
            raise StorageError(f"Index file is missing required key: '{key}'")
        if not isinstance(raw_data[key], dict):
            raise StorageError(f"Index key '{key}' must contain an object")

    meta = raw_data["meta"]
    _require_int(meta.get("page_count", 0), field_name="meta.page_count")
    _require_int(meta.get("token_count", 0), field_name="meta.token_count")

    for document_id, document_raw in raw_data["documents"].items():
        if not isinstance(document_raw, dict):
            raise StorageError(
                f"Document '{document_id}' payload must contain an object"
            )
        if "url" not in document_raw or "length" not in document_raw:
            raise StorageError(
                f"Document '{document_id}' is missing required fields"
            )
        if not isinstance(document_raw["url"], str):
            raise StorageError(f"Document '{document_id}' url must be a string")
        if "text" in document_raw and not isinstance(document_raw["text"], str):
            raise StorageError(f"Document '{document_id}' text must be a string")
        _require_int(document_raw["length"], field_name=f"documents.{document_id}.length")

    for term, term_raw in raw_data["terms"].items():
        if not isinstance(term_raw, dict):
            raise StorageError(f"Term '{term}' payload must contain an object")

        _require_int(
            term_raw.get("document_frequency", 0),
            field_name=f"terms.{term}.document_frequency",
        )

        postings = term_raw.get("postings", {})
        if not isinstance(postings, dict):
            raise StorageError(f"Term '{term}' postings must contain an object")

        for document_id, posting_raw in postings.items():
            if not isinstance(posting_raw, dict):
                raise StorageError(
                    f"Posting '{term}->{document_id}' payload must contain an object"
                )
            _require_int(
                posting_raw.get("term_frequency", 0),
                field_name=f"terms.{term}.postings.{document_id}.term_frequency",
            )

            positions = posting_raw.get("positions", [])
            if not isinstance(positions, list):
                raise StorageError(
                    f"terms.{term}.postings.{document_id}.positions must be a list"
                )
            for index, position in enumerate(positions):
                _require_int(
                    position,
                    field_name=(
                        f"terms.{term}.postings.{document_id}.positions[{index}]"
                    ),
                )

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
