import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest import mock


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "core" / "matters_beads.py"
SPEC = importlib.util.spec_from_file_location("matters_beads", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
matters_beads = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(matters_beads)


class MattersBeadsTests(unittest.TestCase):
    def test_ensure_state_file_writes_default_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            state_path = Path(tmpdir) / "auto-company.json"
            state = matters_beads.ensure_state_file(state_path)
        self.assertEqual(state["schema_version"], 2)
        self.assertIn("authoritative_state_migration", state["matters"])

    def test_build_batch_selects_ready_beads_for_false_conditions(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            state_path = Path(tmpdir) / "auto-company.json"
            matters_beads.save_state(matters_beads.default_state(), state_path)

            with (
                mock.patch.object(
                    matters_beads,
                    "select_actionable_matter",
                    return_value={
                        "matter": "authoritative_state_migration",
                        "false_conditions": [
                            "consensus generated from authoritative state",
                            "scheduler assigns bounded matter bead batches",
                        ],
                    },
                ),
                mock.patch.object(
                    matters_beads,
                    "ready_issues",
                    return_value=[
                        {"id": "auto-company-3hp.1", "title": "Implement consensus renderer from authoritative state"},
                        {"id": "auto-company-3hp.3", "title": "Update auto-loop scheduler to run matter-scoped bead batches"},
                    ],
                ),
                mock.patch.object(
                    matters_beads,
                    "show_issue",
                    side_effect=[
                        {"id": "auto-company-3hp.1", "title": "Implement consensus renderer from authoritative state"},
                        {"id": "auto-company-3hp.3", "title": "Update auto-loop scheduler to run matter-scoped bead batches"},
                    ],
                ),
            ):
                batch = matters_beads.build_batch(state_path)

        self.assertEqual(batch["selected_matter"], "authoritative_state_migration")
        self.assertEqual([issue["id"] for issue in batch["ready_beads"]], ["auto-company-3hp.1", "auto-company-3hp.3"])

    def test_render_consensus_includes_selected_batch_and_open_questions(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            state_path = Path(tmpdir) / "auto-company.json"
            matters_beads.save_state(matters_beads.default_state(), state_path)

            with (
                mock.patch.object(
                    matters_beads,
                    "build_batch",
                    return_value={
                        "selected_matter": "authoritative_state_migration",
                        "selected_title": "Integrate Matters and Beads as authoritative state",
                        "false_conditions": ["consensus generated from authoritative state"],
                        "ready_beads": [
                            {
                                "id": "auto-company-3hp.1",
                                "title": "Implement consensus renderer from authoritative state",
                                "condition": "consensus generated from authoritative state",
                            }
                        ],
                        "all_supporting_beads": [],
                        "fallback_reason": None,
                    },
                ),
                mock.patch.object(
                    matters_beads,
                    "list_open_questions",
                    return_value=[
                        {
                            "id": "auto-company-1vs",
                            "title": "Decide README-ZH localized documentation policy",
                        }
                    ],
                ),
            ):
                rendered = matters_beads.render_consensus(state_path)

        self.assertIn("auto-company-3hp.1", rendered)
        self.assertIn("auto-company-1vs", rendered)
        self.assertIn("generated briefing", rendered)

    def test_reconcile_matter_returns_selected_batch(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            state_path = Path(tmpdir) / "auto-company.json"
            matters_beads.save_state(matters_beads.default_state(), state_path)

            with (
                mock.patch.object(
                    matters_beads,
                    "select_actionable_matter",
                    return_value={
                        "matter": "authoritative_state_migration",
                        "false_conditions": ["consensus generated from authoritative state"],
                    },
                ),
                mock.patch.object(
                    matters_beads,
                    "ensure_issue_for_condition",
                    return_value={"id": "auto-company-3hp.1"},
                ) as ensure_issue,
                mock.patch.object(
                    matters_beads,
                    "build_batch",
                    return_value={
                        "selected_matter": "authoritative_state_migration",
                        "ready_beads": [{"id": "auto-company-3hp.1"}],
                        "false_conditions": ["consensus generated from authoritative state"],
                    },
                ),
            ):
                result = matters_beads.reconcile_matter(state_path)

        ensure_issue.assert_called_once()
        self.assertEqual(result["selected_matter"], "authoritative_state_migration")
        self.assertEqual(result["ready_beads"][0]["id"], "auto-company-3hp.1")


if __name__ == "__main__":
    unittest.main()
