#!/usr/bin/env python3
"""Reconcile false Matter conditions into Beads work items without mutating Matter truth."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from matters_beads import DEFAULT_STATE_PATH, reconcile_matter


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state", type=Path, default=DEFAULT_STATE_PATH, help="Path to the Matters JSON state file.")
    parser.add_argument("--matter", help="Specific matter ID to reconcile. Defaults to the next actionable matter.")
    parser.add_argument("--json", action="store_true", help="Print the reconciliation result as JSON.")
    args = parser.parse_args()

    result = reconcile_matter(args.state, matter_id=args.matter)
    if args.json:
        print(json.dumps(result, indent=2))
        return 0

    selected = result.get("selected_matter")
    if not selected:
        print("No actionable matters found.")
        return 0

    print(f"Selected matter: {selected}")
    for issue in result.get("ready_beads", []):
        print(f"- {issue['id']}: {issue['title']} ({issue['condition']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
