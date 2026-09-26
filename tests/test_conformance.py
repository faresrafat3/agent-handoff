import json
import shutil
import subprocess
import tempfile
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "bin" / "agent-handoff"


def run(*args):
    return subprocess.run(
        [sys.executable, str(CLI), *args],
        text=True, capture_output=True, check=False,
    )


class ConformanceSuiteTests(unittest.TestCase):
    """The suite is the standard, not a test of this tool.

    A case that starts failing means either the implementation regressed or the
    published expectation was wrong. Both need a human; neither may be papered
    over by editing the suite.
    """

    def setUp(self):
        self.result = run("conformance")
        self.data = json.loads(run("conformance", "--json").stdout)

    def test_reference_implementation_conforms(self):
        self.assertTrue(self.data["conforms"], self.data["results"])
        self.assertEqual(self.data["passed"], self.data["total"])

    def test_suite_is_balanced_on_reject_and_accept(self):
        """A suite of only rejections cannot tell a gate from a blunt refusal."""
        expectations = {c["expect"] for c in self.data["results"]}
        self.assertEqual(expectations, {"accept", "reject"})

    def test_every_case_states_why_it_exists(self):
        for case in self.data["results"]:
            self.assertTrue(case["why"].strip(), case["id"])

    def test_case_ids_are_unique(self):
        ids = [c["id"] for c in self.data["results"]]
        self.assertEqual(len(ids), len(set(ids)))

    def test_suite_declares_an_independent_model_free_verifier(self):
        self.assertTrue(self.data["verifier_is_independent"])
        self.assertFalse(self.data["uses_a_model"])
        self.assertEqual(self.data["implementation"], "agent-handoff")

    def test_suite_runs_in_a_temp_dir_and_leaves_nothing_behind(self):
        import tempfile
        before = set(Path(tempfile.gettempdir()).glob("conformance-*"))
        run("conformance")
        after = set(Path(tempfile.gettempdir()).glob("conformance-*"))
        self.assertEqual(before, after, "conformance must clean up its sandbox")

    def test_conformance_is_deterministic(self):
        first = run("conformance", "--json").stdout
        second = run("conformance", "--json").stdout
        self.assertEqual(json.loads(first), json.loads(second))


class CredentialGateTests(unittest.TestCase):
    """G24: a record carrying a credential is refused, not just redacted later.

    Found by conformance case C08, which failed against the reference
    implementation before this gate existed. The suite earning its keep by
    failing is the whole argument for publishing it.
    """

    def test_doctor_refuses_a_handoff_carrying_a_credential(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.assertEqual(run("--root", str(root), "init").returncode, 0)
            task = root / ".agent-workspace" / "tasks" / "T-0001-demo"
            (task / "handoffs").mkdir(parents=True)
            (task / "task.yaml").write_text(
                "schema_version: 1\nkind: Task\nid: T-0001\nslug: demo\n"
                "title: Demo\ntype: chore\nstatus: in_progress\npriority: p2\n"
                "primary_scope: root\naffected_scopes: [root]\ndepends_on: []\n"
                "related:\n  research: []\n  decisions: []\n", encoding="utf-8",
            )
            # the fixture cites these paths, and the doctor checks that every
            # cited path exists — so the sandbox has to contain them
            (root / "bin").mkdir(exist_ok=True)
            (root / "bin" / "agent-handoff").write_text("stub\n", encoding="utf-8")
            (root / "docs").mkdir(exist_ok=True)
            (root / "docs" / "STANDARD.md").write_text("stub\n", encoding="utf-8")
            (task / "spec.md").write_text("# Spec\n\nThe gate refuses a leaked key.\n", encoding="utf-8")
            (task / "plan.md").write_text("# Plan\n\nWrite the fixture, then read the report.\n", encoding="utf-8")
            (task / "validation.md").write_text("# Validation\n\nNot run yet.\n", encoding="utf-8")

            good = (ROOT / "tests" / "fixtures" / "H-20260926-001.md").read_text(encoding="utf-8")
            head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
            leaked = good.replace("0000000000000000000000000000000000000000", head or "0" * 40)
            leaked = leaked.replace(
                "Clean at the time of writing.",
                "Set the api_key = sk-abcdefghijklmnopqrstuvwx before running the suite.",
            )
            (task / "handoffs" / "H-20260926-001.md").write_text(leaked, encoding="utf-8")
            (task / "state.yaml").write_text(
                "schema_version: 1\nkind: TaskState\ntask_id: T-0001\nstate_revision: 1\n"
                "status: in_progress\nphase: handoff\nreadiness: ready\n"
                "next_action: Run `python3 bin/agent-handoff doctor --strict` and read the report.\n"
                "working_tree: clean\nvalidation:\n  status: not_run\n  run_ids: []\n"
                "latest_handoff: H-20260926-001\nexecution: {}\n", encoding="utf-8",
            )

            doctor = run("--root", str(root), "doctor")
            self.assertEqual(doctor.returncode, 1, doctor.stdout)
            self.assertIn("credential", doctor.stdout)

            # the same record without the key must pass, or the gate is a
            # blanket refusal rather than a credential check
            clean = leaked.replace(
                "Set the api_key = sk-abcdefghijklmnopqrstuvwx before running the suite. ",
                "Clean at the time of writing.",
            )
            (task / "handoffs" / "H-20260926-001.md").write_text(clean, encoding="utf-8")
            self.assertEqual(run("--root", str(root), "doctor").returncode, 0)
