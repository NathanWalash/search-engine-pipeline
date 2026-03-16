"""Smoke tests for the initial project scaffold."""

import importlib


MODULES = [
    "src.crawler",
    "src.parser",
    "src.indexer",
    "src.storage",
    "src.search",
    "src.main",
]


def test_modules_importable() -> None:
    """All scaffold modules should be importable."""
    for module_name in MODULES:
        module = importlib.import_module(module_name)
        assert module is not None


def test_main_exposes_entrypoint() -> None:
    """CLI module should expose the main entrypoint."""
    from src.main import main

    assert callable(main)