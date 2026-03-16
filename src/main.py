"""CLI entry point for the search engine tool."""

from dataclasses import dataclass
from typing import Callable, Optional, Sequence

from src.build_pipeline import BuildResult, format_build_summary, run_build_pipeline
from src.indexer import InvertedIndex

PROMPT = "search> "
HELP_TEXT = (
    "Available commands:\n"
    "  build\n"
    "  load\n"
    "  print <word>\n"
    "  find <query>\n"
    "  help\n"
    "  exit"
)


@dataclass
class CLIContext:
    """State kept during one interactive CLI session."""

    index: Optional[InvertedIndex] = None


BuildPipelineFn = Callable[[], BuildResult]


def parse_command(raw_command: str) -> tuple[str, list[str]]:
    """Parse user input into a normalised command and argument list."""
    command_line = raw_command.strip()
    if not command_line:
        raise ValueError("Error: command cannot be empty")

    parts = command_line.split()
    return parts[0].lower(), parts[1:]


def _ensure_no_arguments(command: str, args: Sequence[str]) -> None:
    if args:
        raise ValueError(f"Error: '{command}' does not take arguments")


def dispatch_command(
    command: str,
    args: Sequence[str],
    *,
    context: Optional[CLIContext] = None,
    build_pipeline: Optional[BuildPipelineFn] = None,
) -> tuple[str, bool]:
    """Return a placeholder response for the given command."""
    if command == "help":
        _ensure_no_arguments(command, args)
        return HELP_TEXT, False

    if command == "exit":
        _ensure_no_arguments(command, args)
        return "Exiting search shell.", True

    if command == "build":
        _ensure_no_arguments(command, args)
        if context is None or build_pipeline is None:
            return "Build requested. Pipeline not implemented yet.", False

        build_result = build_pipeline()
        context.index = build_result.index
        return format_build_summary(build_result.summary), False

    if command == "load":
        _ensure_no_arguments(command, args)
        return "Load requested. Storage layer not implemented yet.", False

    if command == "print":
        if not args:
            raise ValueError("Error: word required")
        if len(args) > 1:
            raise ValueError("Error: print expects exactly one word")
        return f"Print requested for '{args[0]}'.", False

    if command == "find":
        if not args:
            raise ValueError("Error: query cannot be empty")
        query = " ".join(args)
        return f"Find requested for '{query}'.", False

    raise ValueError(
        f"Error: unknown command '{command}'. Type 'help' for usage."
    )


def handle_command(
    raw_command: str,
    *,
    context: Optional[CLIContext] = None,
    build_pipeline: Optional[BuildPipelineFn] = None,
) -> tuple[str, bool]:
    """Parse and dispatch user input, returning message and exit state."""
    command, args = parse_command(raw_command)
    return dispatch_command(
        command,
        args,
        context=context,
        build_pipeline=build_pipeline,
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
                build_pipeline=lambda: run_build_pipeline(
                    progress_callback=print,
                ),
            )
        except ValueError as error:
            print(error)
            continue

        print(message)
        if should_exit:
            break


def main() -> None:
    """Run the command-line interface."""
    run_shell()


if __name__ == "__main__":
    main()
