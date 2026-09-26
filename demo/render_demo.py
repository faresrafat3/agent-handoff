#!/usr/bin/env python3
"""Render the killer moment of the demo as a terminal-styled SVG.

A README screenshot is the difference between "interesting" and "I ran it and it
did this". GitHub renders SVG inline, so this needs no external service and no
upload — the file is committed and it works offline.

The content is NOT hand-written. It is the real `doctor` output produced by
`demo/demo.sh` at the moment it rejects a hollow handoff, captured verbatim.
Re-run `make demo-image` after changing the tool and the image follows.

    python3 demo/render_demo.py            # writes demo/doctor-rejects.svg
"""
from __future__ import annotations

import re
import subprocess
import sys
import tempfile
from pathlib import Path

from rich.console import Console
from rich.syntax import Syntax
from rich.table import Table

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "bin" / "agent-handoff"
OUT = ROOT / "demo" / "doctor-rejects.svg"

BAD_HANDOFF = """---
schema_version: 1
kind: Handoff
id: H-20260926-001
task_id: T-0001
session_id: demo
created_at: 2026-09-26T12:00:00Z
state_revision: 1
checkpoint: {commit: HEAD, tree_state: clean, validation_run_ids: []}
workspace: {root: ., git_head: HEAD, branch: main, dirty_paths: []}
objective: Fix the thing.
next_action: continue
blockers: []
sections: [Objective and acceptance target, Confirmed facts and read set,
  Completed, Current operation, Exact next action, Decisions/spec/plan changes,
  Validation evidence, Blockers and questions, Do not repeat / safe shortcuts,
  Stale or contradictory information, Working tree and uncommitted paths]
---
""" + "".join(
    f"\n# {h}\n\ndone\n"
    for h in [
        "Objective and acceptance target", "Confirmed facts and read set", "Completed",
        "Current operation", "Exact next action", "Decisions/spec/plan changes",
        "Validation evidence", "Blockers and questions", "Do not repeat / safe shortcuts",
        "Stale or contradictory information", "Working tree and uncommitted paths",
    ]
)

TASK_YAML = """schema_version: 1
kind: Task
id: T-0001
slug: demo
title: Demo
type: chore
status: in_progress
priority: p2
primary_scope: root
affected_scopes: [root]
depends_on: []
related: {research: [], decisions: []}
"""

STATE_YAML = """schema_version: 1
kind: TaskState
task_id: T-0001
state_revision: 1
status: in_progress
phase: handoff
readiness: ready
next_action: Prove the doctor rejects the record in the transcript.
working_tree: clean
validation: {status: not_run, run_ids: []}
latest_handoff: H-20260926-001
execution: {}
"""


def capture() -> str:
    """Run the real tool and return its real JSON error output."""
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        subprocess.run(["git", "init", "-q", "."], cwd=root, check=True)
        (root / "app.py").write_text("def handler():\n    return 1\n")
        subprocess.run(["git", "add", "-A"], cwd=root, check=True)
        subprocess.run(
            ["git", "-c", "user.email=demo@local", "-c", "user.name=demo", "commit", "-qm", "init"],
            cwd=root, check=True,
        )
        subprocess.run([sys.executable, "-B", str(CLI), "--root", str(root), "init"],
                       capture_output=True, check=True)
        (root / "bin").mkdir(exist_ok=True)
        (root / "bin" / "agent-handoff").write_text((CLI).read_text())
        for schema in (ROOT / "schemas").glob("*.json"):
            (root / ".agent-workspace" / "schema" / schema.name).write_text(schema.read_text())

        task = root / ".agent-workspace" / "tasks" / "T-0001-demo"
        (task / "handoffs").mkdir(parents=True, exist_ok=True)
        (task / "task.yaml").write_text(TASK_YAML)
        (task / "state.yaml").write_text(STATE_YAML)
        (task / "spec.md").write_text("# Spec\n\nThe doctor refuses a hollow record.\n")
        (task / "plan.md").write_text("# Plan\n\nWrite it, then read the report.\n")
        (task / "validation.md").write_text("# Validation\n\nNot run yet.\n")
        (task / "handoffs" / "H-20260926-001.md").write_text(BAD_HANDOFF)

        done = subprocess.run([sys.executable, "-B", str(CLI), "--root", str(root), "doctor"],
                              capture_output=True, text=True)
        assert done.returncode != 0, "the fixture must be rejected; the image would be a lie"
        return done.stdout


def main() -> int:
    raw = capture()
    import json

    data = json.loads(raw)
    errors = [e.splitlines()[0] for e in data["errors"]]
    warnings = [w.splitlines()[0] for w in data["warnings"]]

    console = Console(record=True, width=104, file=open("/dev/null", "w"))
    console.print("[bold]The handoff everyone actually writes[/bold]")
    console.print("[dim]11 sections. All present. Says nothing.[/dim]\n")
    console.print(Syntax(
        "# Objective and acceptance target\ndone\n\n# Completed\ndone\n\n"
        "# Exact next action\ncontinue the work\n\n# Validation evidence\ndone",
        "markdown", theme="ansi_dark", background_color="default", word_wrap=True,
    ))
    console.print()
    console.print("[bold]$ agent-handoff doctor --strict[/bold]")
    console.print(f"[red]reject[/red] {errors[0]}")
    hollow = [e for e in errors if "carries no information" in e]
    if hollow:
        console.print(f"[red]reject[/red] {len(hollow)} sections carry no information "
                      f"[dim](all 11 headings present, none with content)[/dim]")
    restate = [e for e in errors if "restate" in e]
    if restate:
        console.print(f"[red]reject[/red] {restate[0].split(':')[0]}")
    vague = [e for e in errors if "next_action is not actionable" in e]
    if vague:
        detail = vague[0].split("not actionable:")[1].split(" in ")[0].strip()
        console.print(f"[red]reject[/red] handoff next_action is not actionable: {detail}")
    for e in errors:
        if any(k in e for k in ("carries no information", "restate", "next_action is not actionable")):
            continue
        console.print(f"[red]reject[/red] {e}")
    for w in warnings:
        console.print(f"[yellow]warn [/yellow] {w}")
    console.print()
    total = len(errors)
    console.print(f"[bold red]{total} defects[/bold red] [dim]· exit 1 · the record cannot pass[/dim]")
    console.print()
    console.print("[dim]A summary cannot do this. Prose does not fail a build.[/dim]")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    console.save_svg(str(OUT), title="agent-handoff doctor --strict")
    size = OUT.stat().st_size
    print(f"wrote {OUT.relative_to(ROOT)}  ({size // 1024} KB, {total} real findings)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
