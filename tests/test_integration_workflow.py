"""Integration tests for end-to-end CLI command workflow."""

from pathlib import Path
import shutil
import uuid

import src.build_pipeline as build_pipeline
import src.main as main_module
from src.build_pipeline import run_build_pipeline
from src.crawler import CrawledPage
from src.main import handle_command
from src.storage import load_index, save_index


def _make_local_tmp_dir() -> Path:
    temp_dir = Path(".tmp_integration_tests") / str(uuid.uuid4())
    temp_dir.mkdir(parents=True, exist_ok=False)
    return temp_dir


def test_build_load_print_find_workflow(monkeypatch) -> None:
    temp_dir = _make_local_tmp_dir()
    index_path = temp_dir / "index.json"

    pages = [
        CrawledPage(
            url="https://quotes.toscrape.com/page/1/",
            html="<p>Good friends make good times.</p>",
            status_code=200,
        ),
        CrawledPage(
            url="https://quotes.toscrape.com/page/2/",
            html="<p>Truth and kindness.</p>",
            status_code=200,
        ),
    ]

    def fake_crawl_site_bfs(*args, **kwargs):
        del args, kwargs
        return pages

    monkeypatch.setattr(build_pipeline, "crawl_site_bfs", fake_crawl_site_bfs)

    try:
        build_context = main_module.CLIContext()
        build_message, should_exit = handle_command(
            "build",
            context=build_context,
            build_pipeline=lambda: run_build_pipeline(
                start_url="https://quotes.toscrape.com/",
                allowed_domain="quotes.toscrape.com",
                max_pages=10,
            ),
            save_index_fn=lambda index: str(save_index(index, path=index_path)),
        )
        assert should_exit is False
        assert "Build complete." in build_message
        assert "Pages crawled: 2" in build_message
        assert index_path.exists()
        assert build_context.index is not None

        load_context = main_module.CLIContext()
        load_message, should_exit = handle_command(
            "load",
            context=load_context,
            load_index_fn=lambda: (
                load_index(path=index_path),
                str(index_path),
            ),
        )
        assert should_exit is False
        assert load_message == f"Index loaded from: {index_path}"
        assert load_context.index is not None

        print_message, should_exit = handle_command("print good", context=load_context)
        assert should_exit is False
        assert "Word: good" in print_message
        assert "Document frequency: 1" in print_message
        assert "https://quotes.toscrape.com/page/1/" in print_message

        find_message, should_exit = handle_command(
            "find good friends",
            context=load_context,
        )
        assert should_exit is False
        assert "Query: good friends" in find_message
        assert "Matches: 1" in find_message
        assert "https://quotes.toscrape.com/page/1/" in find_message
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
