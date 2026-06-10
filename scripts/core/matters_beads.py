#!/usr/bin/env python3
"""Shared helpers for the Auto-Company Matters + Beads integration."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_STATE_PATH = REPO_ROOT / ".matters" / "auto-company.json"
DEFAULT_CONSENSUS_PATH = REPO_ROOT / "memories" / "consensus.md"
DEFAULT_PARENT_BEAD = "auto-company-3hp"

DEFAULT_STATE = {
    "schema_version": 2,
    "matters": ["authoritative_state_migration"],
    "conditions": {
        "authoritative_state_migration": [
            {"label": "beads holds operational backlog", "truth": True},
            {"label": "matters state file exists", "truth": True},
            {"label": "consensus generated from authoritative state", "truth": False},
            {"label": "scheduler assigns bounded matter bead batches", "truth": False},
            {"label": "reconciler updates matters only from evidence", "truth": False},
        ]
    },
    "dependencies": [],
}

MATTER_DEFINITIONS: dict[str, dict[str, Any]] = {
    "authoritative_state_migration": {
        "title": "Integrate Matters and Beads as authoritative state",
        "phase": "Building",
        "project_label": "Auto-Company framework state migration",
        "product": "Auto Company autonomous operations framework",
        "tech_stack": "Bash, Python, Beads, matters.global CLI",
        "parent_bead": DEFAULT_PARENT_BEAD,
        "conditions": {
            "consensus generated from authoritative state": {
                "bead": {
                    "id": "auto-company-3hp.1",
                    "title": "Implement consensus renderer from authoritative state",
                    "description": (
                        "Create a renderer that makes memories/consensus.md a generated "
                        "briefing from Matters durable state and Beads operational state."
                    ),
                    "acceptance_criteria": (
                        "Renderer produces the existing consensus.md shape or a clearly "
                        "compatible briefing; generated output is deterministic; source "
                        "of truth is not consensus.md."
                    ),
                    "priority": "P2",
                    "type": "task",
                    "labels": ["architecture", "beads", "consensus", "implementation", "matters", "phase-2", "state"],
                }
            },
            "scheduler assigns bounded matter bead batches": {
                "bead": {
                    "id": "auto-company-3hp.3",
                    "title": "Update auto-loop scheduler to run matter-scoped bead batches",
                    "description": (
                        "Change autonomous run prompt selection from open-ended company "
                        "prompt toward selecting the next actionable matter/frontier, "
                        "reconciling that matter into ready beads, and assigning the whole "
                        "ready bead batch for that matter to the run."
                    ),
                    "acceptance_criteria": (
                        "Scheduler can compute/select an actionable matter via matters "
                        "unlock/frontier, reconcile that matter into beads, read bd ready "
                        "--json, select all ready non-epic beads supporting the selected "
                        "matter, include each bead's acceptance criteria in a matter-scoped "
                        "batch prompt, and preserve current loop behavior when no actionable "
                        "matter or bead batch exists."
                    ),
                    "priority": "P2",
                    "type": "task",
                    "labels": ["architecture", "beads", "implementation", "phase-2", "scheduler", "state"],
                }
            },
            "reconciler updates matters only from evidence": {
                "bead": {
                    "id": "auto-company-3hp.2",
                    "title": "Implement matters-to-beads reconciler guardrail",
                    "description": (
                        "Create the smallest reconciler that maps false actionable matter "
                        "conditions to beads and prevents worker agents from declaring "
                        "strategic progress directly."
                    ),
                    "acceptance_criteria": (
                        "Reconciler creates or updates beads for actionable false "
                        "conditions; Matters updates require evidence; worker task flow "
                        "documents that agents update Beads only."
                    ),
                    "priority": "P2",
                    "type": "task",
                    "labels": ["architecture", "beads", "implementation", "matters", "phase-2", "reconciler", "state"],
                }
            },
        },
    }
}


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def slugify(value: str) -> str:
    return "".join(char.lower() if char.isalnum() else "_" for char in value).strip("_")


def resolve_matters_bin() -> str:
    configured = os.environ.get("MATTERS_BIN")
    if configured:
        return configured
    discovered = shutil.which("matters")
    if discovered:
        return discovered
    fallback = Path.home() / "scripts" / "matters"
    return str(fallback)


def run_command(args: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(
        args,
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
    )
    if check and proc.returncode != 0:
        raise RuntimeError(
            f"Command failed ({proc.returncode}): {' '.join(args)}\n"
            f"stdout:\n{proc.stdout}\n"
            f"stderr:\n{proc.stderr}"
        )
    return proc


def run_json_command(args: list[str], *, check: bool = True) -> Any:
    proc = run_command(args, check=check)
    output = (proc.stdout or "").strip()
    if not output:
        return None
    return json.loads(output)


def default_state() -> dict[str, Any]:
    return deepcopy(DEFAULT_STATE)


def ensure_state_file(state_path: Path = DEFAULT_STATE_PATH) -> dict[str, Any]:
    if state_path.exists():
        return load_state(state_path)
    state = default_state()
    save_state(state, state_path)
    return state


def load_state(state_path: Path = DEFAULT_STATE_PATH) -> dict[str, Any]:
    return json.loads(state_path.read_text(encoding="utf-8"))


def save_state(state: dict[str, Any], state_path: Path = DEFAULT_STATE_PATH) -> None:
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")


def get_conditions(state: dict[str, Any], matter_id: str) -> list[dict[str, Any]]:
    return list(state.get("conditions", {}).get(matter_id, []))


def get_false_conditions(state: dict[str, Any], matter_id: str) -> list[str]:
    return [item["label"] for item in get_conditions(state, matter_id) if not item.get("truth")]


def select_actionable_matter(state_path: Path = DEFAULT_STATE_PATH) -> dict[str, Any] | None:
    report = run_json_command([resolve_matters_bin(), "unlock", "--state", str(state_path), "--json"])
    items = list((report or {}).get("items", []))
    if not items:
        return None
    items.sort(key=lambda item: (-int(item.get("impact", 0)), item.get("matter", "")))
    return items[0]


def show_issue(issue_id: str) -> dict[str, Any] | None:
    issue = run_json_command(["bd", "show", issue_id, "--json"], check=False)
    if not issue:
        return None
    if isinstance(issue, list):
        return issue[0]
    return issue


def query_children(parent_id: str) -> list[dict[str, Any]]:
    issues = run_json_command(["bd", "query", f"parent={parent_id}", "--json", "-n", "0", "-a"])
    return list(issues or [])


def ready_issues() -> list[dict[str, Any]]:
    issues = run_json_command(["bd", "ready", "--json"])
    return list(issues or [])


def open_issues(parent_id: str) -> list[dict[str, Any]]:
    return [issue for issue in query_children(parent_id) if issue.get("status") != "closed"]


def bead_spec_for_condition(matter_id: str, condition: str) -> dict[str, Any] | None:
    return MATTER_DEFINITIONS.get(matter_id, {}).get("conditions", {}).get(condition, {}).get("bead")


def sync_issue_metadata(issue: dict[str, Any], matter_id: str, condition: str, parent_bead: str) -> dict[str, Any]:
    metadata = {
        "managed_by": "reconcile-matters-beads",
        "matter": matter_id,
        "condition": condition,
        "condition_slug": slugify(condition),
    }
    current_metadata = dict(issue.get("metadata") or {})
    needs_update = issue.get("parent") != parent_bead or any(
        current_metadata.get(key) != value for key, value in metadata.items()
    )
    if not needs_update:
        return issue

    args = ["bd", "update", issue["id"], "--parent", parent_bead]
    for key, value in metadata.items():
        args.extend(["--set-metadata", f"{key}={value}"])
    result = run_json_command(args + ["--json"])
    if isinstance(result, list):
        return result[0]
    return result


def ensure_issue_for_condition(matter_id: str, condition: str) -> dict[str, Any]:
    spec = bead_spec_for_condition(matter_id, condition)
    if spec is None:
        raise KeyError(f"No bead spec configured for {matter_id!r} / {condition!r}")

    parent_bead = MATTER_DEFINITIONS[matter_id]["parent_bead"]
    issue = show_issue(spec["id"])
    if issue is None:
        args = [
            "bd",
            "create",
            "--id",
            spec["id"],
            "--parent",
            parent_bead,
            "--title",
            spec["title"],
            "--description",
            spec["description"],
            "--acceptance",
            spec["acceptance_criteria"],
            "--priority",
            spec["priority"],
            "--type",
            spec["type"],
            "--json",
        ]
        if spec.get("labels"):
            args.extend(["--labels", ",".join(spec["labels"])])
        issue = run_json_command(args)
        if isinstance(issue, list):
            issue = issue[0]
    issue = sync_issue_metadata(issue, matter_id, condition, parent_bead)
    refreshed = show_issue(spec["id"])
    if refreshed is None:
        raise RuntimeError(f"Bead {spec['id']} was not visible after reconciliation")
    return refreshed


def reconcile_matter(state_path: Path = DEFAULT_STATE_PATH, matter_id: str | None = None) -> dict[str, Any]:
    ensure_state_file(state_path)
    selected = select_actionable_matter(state_path) if matter_id is None else {"matter": matter_id}
    if selected is None:
        return {"selected_matter": None, "created_or_updated": [], "ready_beads": [], "false_conditions": []}

    matter_id = selected["matter"]
    state = load_state(state_path)
    false_conditions = list(selected.get("false_conditions") or get_false_conditions(state, matter_id))
    created_or_updated: list[dict[str, Any]] = []
    for condition in false_conditions:
        if bead_spec_for_condition(matter_id, condition) is None:
            continue
        created_or_updated.append(ensure_issue_for_condition(matter_id, condition))

    batch = build_batch(state_path, selected_matter=selected)
    batch["created_or_updated"] = created_or_updated
    return batch


def build_batch(
    state_path: Path = DEFAULT_STATE_PATH,
    *,
    selected_matter: dict[str, Any] | None = None,
) -> dict[str, Any]:
    ensure_state_file(state_path)
    state = load_state(state_path)
    actionable = selected_matter or select_actionable_matter(state_path)
    if actionable is None:
        return {
            "selected_matter": None,
            "selected_title": None,
            "false_conditions": [],
            "ready_beads": [],
            "all_supporting_beads": [],
            "fallback_reason": "No actionable matters found.",
        }

    matter_id = actionable["matter"]
    matter_def = MATTER_DEFINITIONS.get(matter_id, {})
    false_conditions = list(actionable.get("false_conditions") or get_false_conditions(state, matter_id))
    ready_index = {issue["id"]: issue for issue in ready_issues()}

    supporting_beads: list[dict[str, Any]] = []
    ready_beads_for_matter: list[dict[str, Any]] = []
    for condition in false_conditions:
        spec = bead_spec_for_condition(matter_id, condition)
        if spec is None:
            continue
        issue = show_issue(spec["id"])
        if issue is None:
            continue
        issue["condition"] = condition
        supporting_beads.append(issue)
        ready_issue = ready_index.get(spec["id"])
        if ready_issue is not None:
            combined = dict(issue)
            combined.update(ready_issue)
            combined["condition"] = condition
            ready_beads_for_matter.append(combined)

    supporting_beads.sort(key=lambda issue: issue["id"])
    ready_beads_for_matter.sort(key=lambda issue: issue["id"])

    return {
        "selected_matter": matter_id,
        "selected_title": matter_def.get("title", matter_id),
        "false_conditions": false_conditions,
        "ready_beads": ready_beads_for_matter,
        "all_supporting_beads": supporting_beads,
        "fallback_reason": (
            "Selected matter has no ready supporting beads."
            if false_conditions and not ready_beads_for_matter
            else None
        ),
    }


def list_open_questions(parent_id: str = DEFAULT_PARENT_BEAD, *, exclude_ids: set[str] | None = None) -> list[dict[str, Any]]:
    exclude_ids = exclude_ids or set()
    questions = [issue for issue in open_issues(parent_id) if issue["id"] not in exclude_ids]
    questions.sort(key=lambda issue: (issue.get("priority", 99), issue["id"]))
    return questions


def render_consensus(state_path: Path = DEFAULT_STATE_PATH) -> str:
    ensure_state_file(state_path)
    state = load_state(state_path)
    batch = build_batch(state_path)
    selected_matter = batch["selected_matter"]
    selected_def = MATTER_DEFINITIONS.get(selected_matter or "", {})
    ready_beads_for_matter = batch["ready_beads"]
    ready_ids = {issue["id"] for issue in ready_beads_for_matter}
    open_questions = list_open_questions(exclude_ids=ready_ids)
    open_question_ids = {item["id"] for item in open_questions}
    other_ready = [
        issue
        for issue in ready_issues()
        if issue["id"] not in ready_ids and issue["id"] not in open_question_ids
    ]
    other_ready.sort(key=lambda issue: (issue.get("priority", 99), issue["id"]))

    next_action = "No actionable matter-scoped bead batch is currently available."
    if selected_matter and ready_beads_for_matter:
        bead_ids = ", ".join(issue["id"] for issue in ready_beads_for_matter)
        next_action = (
            f"Work the {selected_matter} batch: {bead_ids}. "
            "Update each bead with evidence and do not mark Matter truth directly."
        )
    elif selected_matter:
        next_action = (
            f"Reconcile the {selected_matter} frontier into ready beads or unblock the next condition."
        )

    lines = [
        "# Auto Company Consensus",
        "",
        "## Last Updated",
        now_utc(),
        "",
        "## Current Phase",
        selected_def.get("phase", "Building"),
        "",
        "## What We Did This Cycle",
        "- Generated this briefing from `.matters/auto-company.json` and the current Beads backlog.",
    ]
    if selected_matter:
        lines.append(
            f"- Selected matter frontier: `{selected_matter}` with {len(batch['false_conditions'])} false actionable condition(s)."
        )
    if ready_beads_for_matter:
        lines.append(
            f"- Ready batch size: {len(ready_beads_for_matter)} bead(s) aligned to the selected matter."
        )
    else:
        lines.append("- No ready matter-scoped bead batch is currently available.")

    lines.extend(
        [
            "",
            "## Key Decisions Made",
            "- Matters is the durable strategic state; Beads is the tactical execution backlog.",
            "- `memories/consensus.md` is a generated briefing and not the source of truth.",
            "",
            "## Active Projects",
        ]
    )
    if selected_matter:
        if ready_beads_for_matter:
            bead_ids = ", ".join(issue["id"] for issue in ready_beads_for_matter)
            lines.append(
                f"- {selected_def.get('project_label', selected_matter)}: in progress — ready batch `{bead_ids}`"
            )
        else:
            lines.append(
                f"- {selected_def.get('project_label', selected_matter)}: in progress — reconcile or unblock the next condition"
            )
    else:
        lines.append("- No active authoritative-state matter selected.")

    lines.extend(
        [
            "",
            "## Next Action",
            next_action,
            "",
            "## Company State",
            f"- Product: {selected_def.get('product', 'Auto Company autonomous operations framework')}",
            f"- Tech Stack: {selected_def.get('tech_stack', 'Bash, Python, Beads, matters.global CLI')}",
            "- Revenue: $0",
            "- Users: 0",
            "",
            "## Open Questions",
        ]
    )

    if open_questions:
        for issue in open_questions:
            lines.append(f"- {issue['id']}: {issue['title']}")
    elif other_ready:
        for issue in other_ready:
            lines.append(f"- {issue['id']}: {issue['title']}")
    else:
        if ready_beads_for_matter:
            lines.append("- None beyond the active matter-scoped batch.")
        else:
            lines.append("- None at the moment.")

    return "\n".join(lines) + "\n"
