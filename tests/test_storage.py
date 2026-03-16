"""Unit tests for index storage save/load behaviour."""

import json
from pathlib import Path
import shutil
import uuid

import pytest

from src.indexer import create_inverted_index
from src.storage import StorageError, load_index, save_index


def _make_local_tmp_dir() -> Path:
    temp_dir = Path(".tmp_storage_tests") / str(uuid.uuid4())
    temp_dir.mkdir(parents=True, exist_ok=False)
    return temp_dir


def test_save_then_load_round_trip() -> None:
    temp_dir = _make_local_tmp_dir()
    index = create_inverted_index()
    index.add_document_terms(
        document_id="doc1",
        url="https://quotes.toscrape.com/page/1/",
        tokens=["friend", "friend", "truth"],
    )
    try:
        path = temp_dir / "index.json"
        saved_path = save_index(index, path=path)
        loaded = load_index(path=saved_path)
        assert loaded.to_dict() == index.to_dict()
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_load_missing_file_raises_file_not_found() -> None:
    temp_dir = _make_local_tmp_dir()
    try:
        missing = temp_dir / "missing.json"
        with pytest.raises(StorageError, match="Index file not found"):
            load_index(path=missing)
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_load_malformed_json_raises_decode_error() -> None:
    temp_dir = _make_local_tmp_dir()
    try:
        malformed = temp_dir / "index.json"
        malformed.write_text("{not-valid-json", encoding="utf-8")
        with pytest.raises(StorageError, match="not valid JSON"):
            load_index(path=malformed)
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_load_missing_required_key_raises_storage_error() -> None:
    temp_dir = _make_local_tmp_dir()
    try:
        invalid = temp_dir / "index.json"
        invalid.write_text(json.dumps({"meta": {}, "documents": {}}), encoding="utf-8")

        with pytest.raises(StorageError, match="missing required key: 'terms'"):
            load_index(path=invalid)
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_save_to_directory_path_raises_storage_error() -> None:
    temp_dir = _make_local_tmp_dir()
    try:
        index = create_inverted_index()
        with pytest.raises(StorageError, match="path is a directory"):
            save_index(index, path=temp_dir)
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_load_from_directory_path_raises_storage_error() -> None:
    temp_dir = _make_local_tmp_dir()
    try:
        with pytest.raises(StorageError, match="path is a directory"):
            load_index(path=temp_dir)
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_load_non_object_json_raises_storage_error() -> None:
    temp_dir = _make_local_tmp_dir()
    try:
        invalid = temp_dir / "index.json"
        invalid.write_text(json.dumps(["not", "an", "object"]), encoding="utf-8")

        with pytest.raises(StorageError, match="must contain a JSON object"):
            load_index(path=invalid)
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_load_with_non_object_terms_raises_storage_error() -> None:
    temp_dir = _make_local_tmp_dir()
    try:
        invalid = temp_dir / "index.json"
        invalid.write_text(
            json.dumps({"meta": {}, "documents": {}, "terms": []}),
            encoding="utf-8",
        )

        with pytest.raises(StorageError, match="key 'terms' must contain an object"):
            load_index(path=invalid)
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
