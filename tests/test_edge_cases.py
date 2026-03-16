"""Additional edge-case coverage for CLI and storage interactions."""

from pathlib import Path
import shutil
import uuid

import pytest

import src.main as main_module
from src.main import handle_command
from src.storage import load_index


def _make_local_tmp_dir() -> Path:
    temp_dir = Path(".tmp_edge_case_tests") / str(uuid.uuid4())
    temp_dir.mkdir(parents=True, exist_ok=False)
    return temp_dir


def test_find_command_with_blank_query_raises_error() -> None:
    with pytest.raises(ValueError, match="query cannot be empty"):
        handle_command("find   ", context=main_module.CLIContext())


def test_load_command_reports_missing_index_file() -> None:
    temp_dir = _make_local_tmp_dir()
    missing = temp_dir / "missing.json"
    context = main_module.CLIContext()

    try:
        with pytest.raises(ValueError, match="Index file not found"):
            handle_command(
                "load",
                context=context,
                load_index_fn=lambda: (load_index(path=missing), str(missing)),
            )
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_load_command_reports_malformed_index_data() -> None:
    temp_dir = _make_local_tmp_dir()
    malformed = temp_dir / "index.json"
    malformed.write_text('{"meta": {"page_count": 1}}', encoding="utf-8")
    context = main_module.CLIContext()

    try:
        with pytest.raises(ValueError, match="missing required key: 'documents'"):
            handle_command(
                "load",
                context=context,
                load_index_fn=lambda: (load_index(path=malformed), str(malformed)),
            )
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
