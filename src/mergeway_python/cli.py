from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from .database import Database


def build_parser() -> argparse.ArgumentParser:
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
    generate.add_argument(
        "--config",
        required=True,
        type=Path,
        help="Path to the mergeway.yaml entry file.",
    )
    generate.add_argument(
        "--cli-binary",
        default="mergeway-cli",
        help="CLI binary name or path.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "generate":
        database = Database(args.config, cli_binary=args.cli_binary)
        output_path = database.generate_classes(args.output)
        print(output_path)
        return 0

    parser.error(f"Unsupported command: {args.command}")
    return 1
