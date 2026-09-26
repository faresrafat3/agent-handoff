import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "bin" / "agent-handoff"

PILE = """# Session handoff

## Current Status
TBD

## Completed
- fixed the tokenizer

## Next Action
continue the work

## git head: a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0

## Blockers
- TODO: ask about the schema

## Notes
Set the api_key = sk-abc123def456ghi789 here temporarily.
"""

CLEAN = """# Architecture

The pipeline reads from S3, normalizes records, and writes to Postgres.
Throughput is roughly 4k records per second per worker. The normalizer is pure
and independently testable, which is why we split it from the writer.
"""


def run(*args, cwd=None):
    return subprocess.run(
        [sys.executable, str(CLI), *args],
        cwd=cwd, text=True, capture_output=True, check=False,
    )


def pile_project(root: Path) -> Path:
    (root / "notes").mkdir(parents=True, exist_ok=True)
    (root / "docs").mkdir(parents=True, exist_ok=True)
    (root / "notes" / "handoff.md").write_text(PILE, encoding="utf-8")
    (root / "docs" / "architecture.md").write_text(CLEAN, encoding="utf-8")
    return root


class AdoptTests(unittest.TestCase):
    def test_adopt_is_read_only_and_creates_nothing(self):
        with tempfile.TemporaryDirectory() as temp:
            root = pile_project(Path(temp))
            before = sorted(p.relative_to(root).as_posix() for p in root.rglob("*"))
            result = run("--root", str(root), "adopt")
            self.assertEqual(result.returncode, 1, result.stdout)
            after = sorted(p.relative_to(root).as_posix() for p in root.rglob("*"))
            self.assertEqual(before, after, "adopt must not write, move, or delete anything")
            self.assertNotIn(".agent-workspace", " ".join(after))

    def test_adopt_finds_each_defect_class(self):
        with tempfile.TemporaryDirectory() as temp:
            root = pile_project(Path(temp))
            data = json.loads(run("--root", str(root), "adopt").stdout)
            kinds = set(data["findings_by_kind"])
            self.assertIn("hollow-section", kinds)
            self.assertIn("vague-next-action", kinds)
            self.assertIn("unknown-commit", kinds)
            self.assertIn("secret-pattern", kinds)

    def test_vague_next_action_is_classified_precisely(self):
        """A vague next action must be named as vague, not merely flagged.

        The `elif not is_actionable(...)` branch also catches filler, so a
        weaker assertion would pass even if the vagueness gate were deleted —
        the finding would just be filed under a different `kind`. Asserting the
        exact classification is what makes this test mutation-sensitive.
        """
        with tempfile.TemporaryDirectory() as temp:
            root = pile_project(Path(temp))
            data = json.loads(run("--root", str(root), "adopt").stdout)
            entry = next(f for f in data["files"] if f["path"].endswith("handoff.md"))
            vague = [f for f in entry["findings"] if f["kind"] == "vague-next-action"]
            self.assertEqual(len(vague), 1, entry["findings"])
            self.assertIn("continue the work", vague[0]["detail"])

    def test_each_defect_in_the_pile_is_found_exactly_once(self):
        with tempfile.TemporaryDirectory() as temp:
            root = pile_project(Path(temp))
            data = json.loads(run("--root", str(root), "adopt").stdout)
            entry = next(f for f in data["files"] if f["path"].endswith("handoff.md"))
            kinds = [f["kind"] for f in entry["findings"]]
            # the pile has exactly one of each planted defect
            self.assertEqual(kinds.count("hollow-section"), 1, kinds)
            self.assertEqual(kinds.count("unknown-commit"), 1, kinds)
            self.assertEqual(kinds.count("secret-pattern"), 1, kinds)
            self.assertEqual(kinds.count("vague-next-action"), 1, kinds)

    def test_adopt_does_not_flag_a_real_document(self):
        with tempfile.TemporaryDirectory() as temp:
            root = pile_project(Path(temp))
            data = json.loads(run("--root", str(root), "adopt").stdout)
            flagged = {f["path"] for f in data["files"]}
            self.assertNotIn("docs/architecture.md", flagged)

    def test_clean_project_exits_zero(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "docs").mkdir()
            (root / "docs" / "architecture.md").write_text(CLEAN, encoding="utf-8")
            result = run("--root", str(root), "adopt")
            self.assertEqual(result.returncode, 0, result.stdout)
            data = json.loads(result.stdout)
            self.assertEqual(data["with_findings"], 0)
            self.assertTrue(data["read_only"])

    def test_every_finding_carries_a_fix(self):
        with tempfile.TemporaryDirectory() as temp:
            root = pile_project(Path(temp))
            data = json.loads(run("--root", str(root), "adopt").stdout)
            for entry in data["files"]:
                for finding in entry["findings"]:
                    self.assertTrue(finding.get("fix"), finding)
                    self.assertTrue(finding.get("detail"), finding)

    def test_adopt_does_not_follow_symlinks_out_of_the_tree(self):
        with tempfile.TemporaryDirectory() as temp, tempfile.TemporaryDirectory() as outside:
            root = pile_project(Path(temp))
            secret = Path(outside) / "secrets.md"
            secret.write_text("## Next Action\nrun rm -rf /\n", encoding="utf-8")
            (root / "notes" / "link.md").symlink_to(secret)
            data = json.loads(run("--root", str(root), "adopt").stdout)
            paths = [f["path"] for f in data["files"]] + [
                f["path"] for f in [{"path": p} for p in data.get("files", [])]
            ]
            self.assertNotIn("notes/link.md", paths)
            self.assertNotIn("outside", json.dumps(data))

    def test_scan_is_bounded_by_limit(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            root.joinpath("docs").mkdir()
            for i in range(12):
                (root / "docs" / f"n{i:02d}.md").write_text(CLEAN, encoding="utf-8")
            data = json.loads(run("--root", str(root), "adopt", "--limit", "5").stdout)
            self.assertEqual(data["scanned"], 5)

    def test_missing_root_is_an_error_not_a_crash(self):
        result = run("--root", "/nonexistent-path-for-adopt-test", "adopt")
        self.assertEqual(result.returncode, 1)
        self.assertNotIn("Traceback", result.stderr)
        self.assertFalse(json.loads(result.stdout)["ok"])
