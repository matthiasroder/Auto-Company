#!/usr/bin/env python3
"""Render memories/consensus.md from Matters and Beads state."""

from __future__ import annotations

import argparse
from pathlib import Path

from matters_beads import DEFAULT_CONSENSUS_PATH, DEFAULT_STATE_PATH, render_consensus


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state", type=Path, default=DEFAULT_STATE_PATH, help="Path to the Matters JSON state file.")
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_CONSENSUS_PATH,
        help="Path to the generated consensus markdown file.",
    )
    parser.add_argument("--stdout", action="store_true", help="Print the rendered briefing instead of writing the file.")
    args = parser.parse_args()

    rendered = render_consensus(args.state)
    if args.stdout:
        print(rendered, end="")
        return 0

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
