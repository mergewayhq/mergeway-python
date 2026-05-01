"""Command-line entrypoints for mergeway."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from .database import Database


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line argument parser."""

    parser = argparse.ArgumentParser(
        prog="mergeway-python",
        description="Python tooling for Mergeway repositories.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    generate = subparsers.add_parser(
        "generate",
        help="Generate Python classes from a mergeway.yaml schema.",
    )
    generate.add_argument("output", type=Path, help="Path to the generated module.")
    location_group = generate.add_mutually_exclusive_group(required=True)
    location_group.add_argument(
        "--config",
        type=Path,
        help="Path to the mergeway.yaml entry file.",
    )
    location_group.add_argument(
        "--root",
        type=Path,
        help="Path to the repository root containing mergeway.yaml.",
    )
    generate.add_argument(
        "--cli-binary",
        default="mergeway-cli",
        help="CLI binary name or path.",
    )
    return parser


def resolve_config_path(args: argparse.Namespace) -> Path:
    """Resolve the config path from parsed CLI arguments."""

    if args.config is not None:
        return args.config
    return args.root / "mergeway.yaml"


def main(argv: Sequence[str] | None = None) -> int:
    """Run the mergeway CLI."""

    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "generate":
        database = Database(resolve_config_path(args), cli_binary=args.cli_binary)
        output_path = database.generate_classes(args.output)
        print(output_path)
        return 0

    parser.error(f"Unsupported command: {args.command}")
    return 1
