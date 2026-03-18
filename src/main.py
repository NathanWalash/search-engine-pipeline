"""CLI entry point for the search engine tool."""

from dataclasses import dataclass
import os
from pathlib import Path
from typing import Callable, Optional, Sequence

from src.benchmarking import format_benchmark_summary, run_benchmark
from src.build_pipeline import BuildResult, format_build_summary, run_build_pipeline
from src.indexer import InvertedIndex
from src.search import (
    RankingMode,
    SUPPORTED_RANKING_MODES,
    find_and_match_documents,
    format_find_results,
    format_term_lookup,
    lookup_term,
    suggest_closest_term,
    suggest_query_terms,
)
from src.storage import DEFAULT_INDEX_PATH, StorageError, load_index, save_index

PROMPT = "search> "
DEFAULT_POLITENESS_SECONDS = 6.0
POLITENESS_ENV_VAR = "SEARCH_POLITENESS_SECONDS"
HELP_TEXT = (
    "Available commands:\n"
    "  build [--incremental]\n"
    "  load\n"
    "  benchmark [--runs N]\n"
    "  print <word>\n"
    "  find [--rank tfidf|bm25] [--proximity-bonus on|off] "
    "[--snippets on|off] <query>\n"
    "  help\n"
    "  exit"
)


@dataclass
class CLIContext:
    """State kept during one interactive CLI session."""

    index: Optional[InvertedIndex] = None


BuildPipelineFn = Callable[..., BuildResult]
SaveIndexFn = Callable[[InvertedIndex], str]
LoadIndexFn = Callable[[], tuple[InvertedIndex, str]]


def parse_command(raw_command: str) -> tuple[str, list[str]]:
    """Parse user input into a normalised command and argument list."""
    command_line = raw_command.strip()
    if not command_line:
        raise ValueError("Error: command cannot be empty")

    parts = command_line.split()
    return parts[0].lower(), parts[1:]


def _ensure_no_arguments(command: str, args: Sequence[str]) -> None:
    """Raise when a command that takes no args receives extra tokens."""
    if args:
        raise ValueError(f"Error: '{command}' does not take arguments")


def _require_loaded_index(context: CLIContext) -> InvertedIndex:
    """Return the loaded index from context or raise a user-facing error."""
    if context.index is None:
        raise ValueError("Error: no index loaded. Run 'build' or 'load' first")
    return context.index


def _read_politeness_seconds() -> float:
    """Return politeness delay from env or fallback to coursework-safe default."""
    raw_value = os.getenv(POLITENESS_ENV_VAR)
    if raw_value is None or not raw_value.strip():
        return DEFAULT_POLITENESS_SECONDS

    try:
        value = float(raw_value)
    except ValueError as exc:
        raise ValueError(
            f"Error: {POLITENESS_ENV_VAR} must be a positive number"
        ) from exc

    if value <= 0:
        raise ValueError(f"Error: {POLITENESS_ENV_VAR} must be greater than 0")
    return value


def _format_suggestions(suggestions: dict[str, str]) -> str:
    """Render one or more spelling suggestions as user-facing text."""
    if not suggestions:
        return ""
    if len(suggestions) == 1:
        return f"Did you mean: {next(iter(suggestions.values()))}?"

    lines = ["Did you mean:"]
    for raw_term, suggested in suggestions.items():
        lines.append(f"- {raw_term} -> {suggested}")
    return "\n".join(lines)


def _parse_find_arguments(
    args: Sequence[str],
) -> tuple[RankingMode, bool, bool, list[str]]:
    """Extract optional find flags and return ranking, flags, and query."""
    if not args:
        raise ValueError("Error: query cannot be empty")

    mode_raw = "tfidf"
    proximity_bonus_raw = "off"
    snippets_raw = "off"
    query_terms: list[str] = []
    position = 0
    while position < len(args):
        token = args[position]
        if token == "--rank":
            if position + 1 >= len(args):
                raise ValueError("Error: --rank requires one of: tfidf, bm25")
            mode_raw = args[position + 1].lower().strip()
            position += 2
            continue
        if token.startswith("--rank="):
            mode_raw = token.split("=", 1)[1].lower().strip()
            position += 1
            continue
        if token == "--proximity-bonus":
            if position + 1 >= len(args):
                raise ValueError("Error: --proximity-bonus requires one of: on, off")
            proximity_bonus_raw = args[position + 1].lower().strip()
            position += 2
            continue
        if token.startswith("--proximity-bonus="):
            proximity_bonus_raw = token.split("=", 1)[1].lower().strip()
            position += 1
            continue
        if token == "--snippets":
            if position + 1 >= len(args):
                raise ValueError("Error: --snippets requires one of: on, off")
            snippets_raw = args[position + 1].lower().strip()
            position += 2
            continue
        if token.startswith("--snippets="):
            snippets_raw = token.split("=", 1)[1].lower().strip()
            position += 1
            continue

        query_terms.append(token)
        position += 1

    if not query_terms:
        raise ValueError("Error: query cannot be empty")

    if mode_raw == "tfidf":
        ranking_mode: RankingMode = "tfidf"
    elif mode_raw == "bm25":
        ranking_mode = "bm25"
    else:
        supported_modes = ", ".join(sorted(SUPPORTED_RANKING_MODES))
        raise ValueError(
            f"Error: unsupported ranking mode '{mode_raw}'. Use one of: {supported_modes}"
        )

    if proximity_bonus_raw not in {"on", "off"}:
        raise ValueError(
            "Error: unsupported proximity bonus mode "
            f"'{proximity_bonus_raw}'. Use one of: on, off"
        )
    if snippets_raw not in {"on", "off"}:
        raise ValueError(
            "Error: unsupported snippets mode "
            f"'{snippets_raw}'. Use one of: on, off"
        )

    return (
        ranking_mode,
        proximity_bonus_raw == "on",
        snippets_raw == "on",
        query_terms,
    )


def _parse_benchmark_arguments(args: Sequence[str]) -> int:
    """Extract benchmark options and return runs count."""
    if not args:
        return 5

    runs_raw: Optional[str] = None
    if len(args) == 2 and args[0] == "--runs":
        runs_raw = args[1]
    elif len(args) == 1 and args[0].startswith("--runs="):
        runs_raw = args[0].split("=", 1)[1]
    else:
        raise ValueError("Error: usage: benchmark [--runs N]")

    try:
        runs = int(runs_raw)
    except ValueError as exc:
        raise ValueError("Error: benchmark runs must be a positive integer") from exc
    if runs <= 0:
        raise ValueError("Error: benchmark runs must be a positive integer")
    return runs


def _parse_build_arguments(args: Sequence[str]) -> bool:
    """Return whether build should run in incremental mode."""
    if not args:
        return False
    if len(args) == 1 and args[0] in {"--incremental", "--incremental=true"}:
        return True
    raise ValueError("Error: usage: build [--incremental]")


def dispatch_command(
    command: str,
    args: Sequence[str],
    *,
    context: Optional[CLIContext] = None,
    build_pipeline: Optional[BuildPipelineFn] = None,
    save_index_fn: Optional[SaveIndexFn] = None,
    load_index_fn: Optional[LoadIndexFn] = None,
) -> tuple[str, bool]:
    """Execute one parsed command and return message plus exit flag."""
    if command == "help":
        _ensure_no_arguments(command, args)
        return HELP_TEXT, False

    if command == "exit":
        _ensure_no_arguments(command, args)
        return "Exiting search shell.", True

    if command == "build":
        use_incremental = _parse_build_arguments(args)
        if context is None or build_pipeline is None:
            if use_incremental:
                return "Build requested (incremental). Pipeline not implemented yet.", False
            return "Build requested. Pipeline not implemented yet.", False

        if use_incremental:
            try:
                build_result = build_pipeline(
                    incremental=True,
                    existing_index=context.index,
                )
            except TypeError:
                build_result = build_pipeline()
        else:
            build_result = build_pipeline()
        context.index = build_result.index
        summary = format_build_summary(build_result.summary)

        if save_index_fn is None:
            return summary, False

        try:
            saved_path = save_index_fn(build_result.index)
        except StorageError as exc:
            raise ValueError(f"Error: {exc}") from exc

        return f"{summary}\nIndex saved to: {saved_path}", False

    if command == "load":
        _ensure_no_arguments(command, args)
        if context is None or load_index_fn is None:
            return "Load requested. Storage layer not implemented yet.", False

        try:
            loaded_index, loaded_path = load_index_fn()
        except StorageError as exc:
            raise ValueError(f"Error: {exc}") from exc

        context.index = loaded_index
        return f"Index loaded from: {loaded_path}", False

    if command == "print":
        if not args:
            raise ValueError("Error: word required")
        if len(args) > 1:
            raise ValueError("Error: print expects exactly one word")
        if context is None:
            return f"Print requested for '{args[0]}'.", False
        index = _require_loaded_index(context)

        lookup = lookup_term(index, args[0])
        if lookup is None:
            suggestion = suggest_closest_term(index, args[0])
            if suggestion is None:
                return "Word not found in index", False
            return f"Word not found in index\nDid you mean: {suggestion}?", False
        return format_term_lookup(lookup), False

    if command == "find":
        (
            ranking_mode,
            use_proximity_bonus,
            use_snippets,
            query_terms,
        ) = _parse_find_arguments(args)
        if context is None:
            query = " ".join(query_terms)
            return f"Find requested for '{query}'.", False
        index = _require_loaded_index(context)

        matches = find_and_match_documents(
            index,
            query_terms,
            ranking_mode=ranking_mode,
            proximity_bonus=use_proximity_bonus,
            include_snippets=use_snippets,
        )
        if not matches:
            suggestions = suggest_query_terms(index, query_terms)
            if not suggestions:
                return "No matching pages found.", False
            return (
                "No matching pages found.\n"
                f"{_format_suggestions(suggestions)}"
            ), False
        return format_find_results(query_terms, matches), False

    if command == "benchmark":
        runs = _parse_benchmark_arguments(args)
        if context is None:
            return "Benchmark requested. Benchmark harness not implemented yet.", False
        index = _require_loaded_index(context)
        benchmark_summary = run_benchmark(index, runs=runs)
        return format_benchmark_summary(benchmark_summary), False

    raise ValueError(
        f"Error: unknown command '{command}'. Type 'help' for usage."
    )


def handle_command(
    raw_command: str,
    *,
    context: Optional[CLIContext] = None,
    build_pipeline: Optional[BuildPipelineFn] = None,
    save_index_fn: Optional[SaveIndexFn] = None,
    load_index_fn: Optional[LoadIndexFn] = None,
) -> tuple[str, bool]:
    """Parse and dispatch user input, returning message and exit state."""
    command, args = parse_command(raw_command)
    return dispatch_command(
        command,
        args,
        context=context,
        build_pipeline=build_pipeline,
        save_index_fn=save_index_fn,
        load_index_fn=load_index_fn,
    )


def run_shell() -> None:
    """Run an interactive command loop."""
    print("Search Engine CLI")
    print("Type 'help' for available commands.")
    context = CLIContext()

    while True:
        try:
            raw_command = input(PROMPT)
        except EOFError:
            print("Exiting search shell.")
            break
        except KeyboardInterrupt:
            print("\nExiting search shell.")
            break

        try:
            message, should_exit = handle_command(
                raw_command,
                context=context,
                build_pipeline=lambda incremental=False, existing_index=None: run_build_pipeline(
                    min_delay_seconds=_read_politeness_seconds(),
                    progress_callback=print,
                    incremental=incremental,
                    existing_index=existing_index,
                ),
                save_index_fn=lambda index: str(
                    save_index(index, path=DEFAULT_INDEX_PATH)
                ),
                load_index_fn=lambda: (
                    load_index(path=DEFAULT_INDEX_PATH),
                    str(Path(DEFAULT_INDEX_PATH)),
                ),
            )
        except ValueError as error:
            print(error)
            continue
        except Exception as error:  # pragma: no cover - defensive guard
            print(f"Error: unexpected failure: {error}")
            continue

        print(message)
        if should_exit:
            break


def main() -> None:
    """Run the command-line interface."""
    run_shell()


if __name__ == "__main__":
    main()
