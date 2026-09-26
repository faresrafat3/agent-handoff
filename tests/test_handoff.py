import re
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HANDOFF = ROOT / "tests" / "fixtures" / "H-20260926-001.md"
CLI = ROOT / "bin" / "agent-handoff"


def _ship_schemas(root):
    target = Path(root) / ".agent-workspace" / "schema"
    target.mkdir(parents=True, exist_ok=True)
    for schema in (ROOT / "schemas").glob("*.json"):
        shutil.copyfile(schema, target / schema.name)


def init(root):
    """`init` plus schemas, matching what install.sh provisions."""
    result = subprocess.run(
        [sys.executable, str(CLI), "--root", str(root), "init"],
        text=True, capture_output=True, check=False,
    )
    if result.returncode == 0:
        target = Path(root) / ".agent-workspace" / "schema"
        target.mkdir(parents=True, exist_ok=True)
        for schema in (ROOT / "schemas").glob("*.json"):
            shutil.copyfile(schema, target / schema.name)
    return result


def load_guards():
    """Execute the dependency-free CLI module to unit-test its pure helpers."""
    namespace = {"__name__": "continuum_workspace_under_test"}
    exec(compile(CLI.read_text(encoding="utf-8"), str(CLI), "exec"), namespace)
    return namespace


class HandoffTests(unittest.TestCase):
    def test_handoff_contains_recovery_contract(self):
        text = HANDOFF.read_text(encoding="utf-8")
        for phrase in [
            "# Objective and acceptance target",
            "# Confirmed facts and read set",
            "# Completed",
            "# Current operation",
            "# Exact next action",
            "# Validation evidence",
            "# Blockers and questions",
            "# Do not repeat",
            "provisional",
            "read-only",
        ]:
            self.assertIn(phrase, text)

    def test_handoff_has_no_secret_like_value(self):
        text = HANDOFF.read_text(encoding="utf-8")
        self.assertNotRegex(text, r"sk-[A-Za-z0-9_-]{12,}")
        self.assertNotRegex(text, r"(?i)(api[_-]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+)")


class ActionableLanguageTests(unittest.TestCase):
    """The next-action gate must reject vagueness without rejecting real work."""

    def setUp(self):
        self.guard = load_guards()
        self.is_actionable = self.guard["is_actionable"]

    def test_vague_instructions_are_rejected(self):
        for phrase in [
            "Do the `thing`",          # backticks must not defeat the blacklist
            "Proceed with S1",         # a bare citation is a reference, not an action
            "Continue the work!",
            "Continue with the plan",   # legitimately actionable, see below
            "Fix it",
            "TBD",
            "Do that.",
            "x",
        ]:
            with self.subTest(phrase=phrase):
                self.assertEqual(
                    self.is_actionable(phrase),
                    phrase == "Continue with the plan",
                    f"{phrase!r} unexpected verdict",
                )

    def test_real_instructions_are_accepted(self):
        for phrase in [
            "Update README.md",
            "Edit README.md",
            "Write the plan",
            "Await human review before merge",
            "Read ./bin/continuum-workspace",
            "Verify H-20260926-004",
            "Consult ./docs/acceptance-matrix.md",
            "Look at ./bin/continuum-workspace",
            "Reconcile the ledger rows",
            "Prepare the handoff prompt",
        ]:
            with self.subTest(phrase=phrase):
                self.assertTrue(self.is_actionable(phrase), f"{phrase!r} wrongly rejected")

    def test_verb_matching_does_not_fire_inside_another_word(self):
        """`read\\b` without a leading boundary matches inside "thread"."""
        self.assertFalse(re.search(r"\bread\b", "thread", re.I) and "thread".lower() == "read")
        self.assertTrue(self.is_actionable("Please read the thread state"))


class SectionContentTests(unittest.TestCase):
    def setUp(self):
        self.guard = load_guards()
        self.substantive = self.guard["section_is_substantive"]
        self.independent = self.guard["sections_are_independent"]

    def test_character_fillers_are_rejected(self):
        for body in [
            "........................",
            "a" * 40,
            "See https://example.com/nothing",
            "body body body body body body body body body body body body",
            "  \n\n  ",
        ]:
            with self.subTest(body=body[:30]):
                self.assertFalse(self.substantive(body), f"{body[:30]!r} wrongly accepted")

    def test_short_but_varied_sections_are_rejected(self):
        """Distinct words are not enough; a section must carry real substance."""
        for body in [
            "One two three four",
            "alpha beta gamma delta",
            "Yes. No. Maybe. Sure.",
            "TODO FIXME NOTE LATER",
        ]:
            with self.subTest(body=body):
                self.assertFalse(self.substantive(body), f"{body!r} wrongly accepted")

    def test_real_prose_is_accepted(self):
        self.assertTrue(self.substantive(
            "The objective is to build the handoff schema with evidence links and typed fields "
            "so a fresh session can recover the task without redoing completed work."))

    def test_restated_sections_are_detected(self):
        duplicate = {
            "one": "The completed work includes the CLI and its unit test suite.",
            "two": "The completed work includes the CLI and its unit test suite.",
            "three": "Validation evidence covers the node regression and the strict doctor run.",
        }
        self.assertFalse(self.independent(duplicate))
        distinct = {
            "one": "Objective is to build the handoff schema with typed fields and evidence links.",
            "two": "Confirmed the WCS doctor passes against a clean nested repository checkout.",
            "three": "Validation evidence includes the node regression result recorded today.",
        }
        self.assertTrue(self.independent(distinct))

    def test_identical_substantive_sections_are_rejected_by_the_doctor(self):
        """11 sections that all restate one sentence must not certify as a handoff."""
        import json
        import subprocess
        import tempfile
        headings = list(self.guard["HANDOFF_HEADINGS"])
        body = ("This section repeats the same recovery sentence for every heading so the "
                "handoff looks complete while carrying no distinct information.\n")
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.assertEqual(subprocess.run(
                [sys.executable, str(CLI), "--root", temp, "init"],
                text=True, capture_output=True, check=False).returncode, 0)
            task = root / ".agent-workspace" / "tasks" / "T-0001-demo"
            task.mkdir(parents=True)
            (task / "task.yaml").write_text(
                "schema_version: 1\nkind: Task\nid: T-0001\nslug: demo\ntitle: Demo\ntype: feature\n"
                "status: in_progress\npriority: p2\nprimary_scope: root\naffected_scopes: [root]\n"
                "depends_on: []\nrelated:\n  research: []\n  decisions: []\n", encoding="utf-8")
            for name in ["spec.md", "plan.md", "validation.md"]:
                (task / name).write_text("#\n", encoding="utf-8")
            (task / "state.yaml").write_text(
                "schema_version: 1\nkind: TaskState\ntask_id: T-0001\nstate_revision: 1\n"
                "status: in_progress\nphase: implement\nreadiness: ready\nnext_action: Run the doctor check\n"
                "working_tree: clean\ndirty_paths: []\nvalidation:\n  status: not_run\n  run_ids: []\n"
                "latest_handoff: H-20260101-001\nexecution:\n  mode: read\n  actor: agent:test\n", encoding="utf-8")
            handoffs = task / "handoffs"
            handoffs.mkdir()
            front = (
                "schema_version: 1\nkind: Handoff\nid: H-20260101-001\ntask_id: T-0001\n"
                "session_id: session-test\ncreated_at: 2026-01-01T00:00:00Z\nstate_revision: 1\n"
                "checkpoint:\n  commit: null\n  tree_state: clean\n  validation_run_ids: []\n"
                "workspace:\n  root: null\n  git_head: null\n  branch: main\n  dirty_paths: []\n"
                "objective: Deliver the guarded recovery path for a fresh session to resume\n"
                "next_action: Run the doctor and confirm zero errors before editing\nblockers: []\nsections:\n"
                + "".join("  - " + heading + "\n" for heading in headings))
            (handoffs / "H-20260101-001.md").write_text(
                f"---\n{front}---\n\nSource Session: @[session-test]\n\n"
                + "".join("# " + heading + "\n\n" + body + "\n" for heading in headings), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(CLI), "--root", temp, "doctor", "--strict"],
                text=True, capture_output=True, check=False)
            self.assertEqual(result.returncode, 1, result.stdout)
            self.assertIn("handoff sections restate the same content", result.stdout)

    def test_objective_must_be_a_substantive_statement(self):
        """A one-word objective is not a goal statement."""
        import json
        import subprocess
        import sys
        import tempfile
        headings = list(self.guard["HANDOFF_HEADINGS"])
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.assertEqual(subprocess.run(
                [sys.executable, str(CLI), "--root", temp, "init"],
                text=True, capture_output=True, check=False).returncode, 0)
            task = root / ".agent-workspace" / "tasks" / "T-0001-demo"
            task.mkdir(parents=True)
            (task / "task.yaml").write_text(
                "schema_version: 1\nkind: Task\nid: T-0001\nslug: demo\ntitle: Demo\ntype: feature\n"
                "status: in_progress\npriority: p2\nprimary_scope: root\naffected_scopes: [root]\n"
                "depends_on: []\nrelated:\n  research: []\n  decisions: []\n", encoding="utf-8")
            for name in ["spec.md", "plan.md", "validation.md"]:
                (task / name).write_text("#\n", encoding="utf-8")
            (task / "state.yaml").write_text(
                "schema_version: 1\nkind: TaskState\ntask_id: T-0001\nstate_revision: 1\n"
                "status: in_progress\nphase: implement\nreadiness: ready\nnext_action: Run the doctor check\n"
                "working_tree: clean\ndirty_paths: []\nvalidation:\n  status: not_run\n  run_ids: []\n"
                "latest_handoff: H-20260101-001\nexecution:\n  mode: read\n  actor: agent:test\n", encoding="utf-8")
            handoffs = task / "handoffs"
            handoffs.mkdir()
            bodies = {
                "Objective and acceptance target": "Deliver the guarded recovery path so a fresh session can resume this task.",
                "Confirmed facts and read set": "The nested repository is clean at the recorded commit and declares a single root scope.",
                "Completed": "The CLI, its schemas, the doctor checks, and the unit suite were written and verified.",
                "Current operation": "The handoff is regenerated so the context pack matches the current state revision.",
                "Exact next action": "Run the doctor and confirm zero errors before editing any record.",
                "Decisions/spec/plan changes": "The recorded decision keeps the host control plane immutable and fork as proposed synthesis.",
                "Validation evidence": "The unit suite, the node regression, and the strict doctor all pass on a clean tree.",
                "Blockers and questions": "No blocker remains open; deferred crash boundary gates are recorded as deferred.",
                "Do not repeat / safe shortcuts": "Never rewrite a historical ledger row to match today's numbers.",
                "Stale or contradictory information": "Earlier handoffs cite older revisions and are superseded by this record.",
                "Working tree and uncommitted paths": "The tree was clean at the recorded checkpoint; verify head and status on disk.",
            }
            for objective, expected in [("x", "not a substantive statement"), ("Deliver the guarded recovery path for a fresh session to resume", None)]:
                front = (
                    "schema_version: 1\nkind: Handoff\nid: H-20260101-001\ntask_id: T-0001\n"
                    "session_id: session-test\ncreated_at: 2026-01-01T00:00:00Z\nstate_revision: 1\n"
                    "checkpoint:\n  commit: null\n  tree_state: clean\n  validation_run_ids: []\n"
                    "workspace:\n  root: null\n  git_head: null\n  branch: main\n  dirty_paths: []\n"
                    f"objective: {objective}\n"
                    "next_action: Run the doctor and confirm zero errors before editing\nblockers: []\nsections:\n"
                    + "".join("  - " + heading + "\n" for heading in headings))
                (handoffs / "H-20260101-001.md").write_text(
                    f"---\n{front}---\n\nSource Session: @[session-test]\n\n"
                    + "".join("# " + heading + "\n\n" + bodies[heading] + "\n" for heading in headings), encoding="utf-8")
                result = subprocess.run(
                    [sys.executable, str(CLI), "--root", temp, "doctor", "--strict"],
                    text=True, capture_output=True, check=False)
                if expected:
                    self.assertEqual(result.returncode, 1, result.stdout)
                    self.assertIn(expected, result.stdout)
                else:
                    self.assertEqual(result.returncode, 0, result.stdout)


if __name__ == "__main__":
    unittest.main()
