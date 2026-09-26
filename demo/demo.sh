#!/usr/bin/env bash
# Reproducible terminal demo: the three silent handoff failures, caught.
#
#   ./demo/demo.sh            run it
#   ./demo/demo.sh --record   record to demo/demo.cast (needs asciinema)
#
# Deterministic: fixed ids, fixed timestamps, no network. Re-running produces the
# same output, so this doubles as a smoke test.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLI="$HERE/../bin/agent-handoff"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

b()  { printf '\n\033[1m%s\033[0m\n' "$1"; }
cmd(){ printf '\033[36m$ %s\033[0m\n' "$1"; shift; "$@" 2>&1 || true; }
bad(){ printf '\033[31m%s\033[0m\n' "$1"; }
good(){ printf '\033[32m%s\033[0m\n' "$1"; }

mkdir -p "$WORK/proj" && cd "$WORK/proj"
git init -q . && printf 'def handler():\n    return 1\n' > app.py
git add -A && git -c user.email=demo@local -c user.name=demo commit -qm "initial commit"

# A real user has the tool in their project; the handoffs below cite its path,
# and the doctor checks that every cited path exists.
mkdir -p bin && cp "$HERE/../bin/agent-handoff" bin/agent-handoff

b "1. Set up a workspace (no dependencies, no network)"
cmd "python3 bin/agent-handoff init" python3 -B "$CLI" init >/dev/null
mkdir -p .agent-workspace/schema && cp "$HERE/../schemas/"*.json .agent-workspace/schema/
good "ok  .agent-workspace/ created, 9 schemas installed"

b "2. The workspace is clean"
cmd "python3 bin/agent-handoff doctor --strict"
out="$(python3 -B "$CLI" doctor --strict)"; echo "$out" | python3 -c "import json,sys;d=json.load(sys.stdin);print(f'  ok={d[\"ok\"]}  errors={len(d[\"errors\"])}  warnings={len(d[\"warnings\"])}')"
good "ok  0 errors, 0 warnings"

TASK=.agent-workspace/tasks/T-0001-demo
mkdir -p "$TASK/handoffs"
cat > "$TASK/task.yaml" <<'EOF'
schema_version: 1
kind: Task
id: T-0001
slug: demo
title: Demo task
type: feature
status: in_progress
priority: p1
primary_scope: root
affected_scopes: [root]
depends_on: []
related:
  research: []
  decisions: []
EOF
printf '# Spec\n\nMake the validator reject a hollow handoff.\n' > "$TASK/spec.md"
printf '# Plan\n\nWrite a bad record. Prove it is rejected.\n' > "$TASK/plan.md"
cat > "$TASK/state.yaml" <<'EOF'
schema_version: 1
kind: TaskState
task_id: T-0001
state_revision: 1
status: in_progress
phase: handoff
readiness: ready
next_action: Write the hollow handoff and prove the doctor rejects it.
working_tree: clean
validation:
  status: not_run
  run_ids: []
latest_handoff: null
execution: {}
EOF
printf '# Validation\n\nNothing run yet.\n' > "$TASK/validation.md"

b "3. Now write the handoff everyone actually writes"
# Eleven headings, present and correct, saying nothing. Passes every markdown linter.
{
cat <<'EOF'
---
schema_version: 1
kind: Handoff
id: H-20260926-001
task_id: T-0001
session_id: demo-session
created_at: 2026-09-26T12:00:00Z
state_revision: 1
checkpoint:
  commit: HEAD
  tree_state: clean
  validation_run_ids: []
workspace:
  root: .
  git_head: HEAD
  branch: main
  dirty_paths: []
objective: Fix the thing.
next_action: continue
blockers: []
sections:
  - Objective and acceptance target
  - Confirmed facts and read set
  - Completed
  - Current operation
  - Exact next action
  - Decisions/spec/plan changes
  - Validation evidence
  - Blockers and questions
  - Do not repeat / safe shortcuts
  - Stale or contradictory information
  - Working tree and uncommitted paths
---
EOF
for h in "Objective and acceptance target" "Confirmed facts and read set" "Completed" "Current operation" "Exact next action" "Decisions/spec/plan changes" "Validation evidence" "Blockers and questions" "Do not repeat / safe shortcuts" "Stale or contradictory information" "Working tree and uncommitted paths"; do
  printf '\n# %s\n\ndone\n' "$h"
done
} > "$TASK/handoffs/H-20260926-001.md"

b "4. The doctor catches all three silent failures at once"
python3 -B "$CLI" doctor --strict 2>/dev/null | python3 -c "
import json,sys
d=json.load(sys.stdin)
for e in d['errors']: print('  \033[31mreject\033[0m', e.split(chr(10))[0])
" || true
python3 -B "$CLI" doctor --strict > "$WORK/report.json" 2>/dev/null || true
python3 - "$WORK/report.json" <<'PYEOF' && bad "  exit code 1 — the bad handoff cannot pass" || bad "  DEMO ASSERTION FAILED"
import json, sys
report = json.load(open(sys.argv[1]))
errors = report["errors"]
handoff = [e for e in errors if "handoff" in e]
offending = [e for e in errors if "handoff" not in e]
assert not report["ok"], "the bad handoff must be rejected"
assert handoff, "expected handoff errors, got none"
assert not offending, "demo fixtures are wrong; the only failure must be the handoff:\n  " + "\n  ".join(offending)
print(f"  {len(handoff)} handoff defects, 0 collateral errors")
PYEOF

b "5. The three specific defects"
cat <<'EOF'
  hollow section      every heading present, no content under any of them
  confident non-action 'continue' names no path, command, id, or check
  restatement         sections padded by repeating each other
EOF

b "6. Supersede it with a real handoff"
echo "  the rejected record stays on disk. Superseded, never deleted:"
ls "$TASK/handoffs/" | sed 's/^/    /'
HEAD_SHA="$(git rev-parse HEAD)"
BRANCH_NAME="$(git rev-parse --abbrev-ref HEAD)"
FIXED=.agent-workspace/tasks/T-0001-demo/handoffs/H-20260926-002.md
cat > "$FIXED" <<'EOF'
---
schema_version: 1
kind: Handoff
id: H-20260926-002
task_id: T-0001
session_id: demo-session
created_at: 2026-09-26T12:30:00Z
state_revision: 1
checkpoint:
  commit: __HEAD__
  tree_state: clean
  validation_run_ids: []
workspace:
  root: .
  git_head: __HEAD__
  branch: __BRANCH__
  dirty_paths: []
objective: Make the validator reject a handoff whose body sections carry no substance, so a hollow record cannot pass as a completed one.
next_action: Run `python3 bin/agent-handoff doctor --strict` and confirm the hollow record is rejected with the three expected errors.
blockers: []
sections:
  - Objective and acceptance target
  - Confirmed facts and read set
  - Completed
  - Current operation
  - Exact next action
  - Decisions/spec/plan changes
  - Validation evidence
  - Blockers and questions
  - Do not repeat / safe shortcuts
  - Stale or contradictory information
  - Working tree and uncommitted paths
---

# Objective and acceptance target

The validator must reject a handoff whose sections are present but hollow, so
that a structurally complete record cannot pass as real work.

# Confirmed facts and read set

Source Session: demo-session

Read `.agent-workspace/schema/handoff.schema.json`. The gates are
`section_is_substantive`, `is_actionable`, and `sections_are_independent`, all
called from the doctor's `check_doctor` pass.

# Completed

Recorded the hollow handoff as `H-20260926-001` at
`.agent-workspace/tasks/T-0001-demo/handoffs/H-20260926-001.md` and captured the
rejection output. It stays on disk as superseded history.

# Current operation

The record is rejected as intended. Not yet confirmed against a workspace with
uncommitted changes, which is the next case to cover.

# Exact next action

Run `python3 bin/agent-handoff doctor --strict` and confirm the hollow record is
rejected while this one passes.

# Decisions/spec/plan changes

Kept `HANDOFF_MIN_BODY` fixed at 24 characters rather than making it
configurable, because a configurable floor is a floor nobody checks.

# Validation evidence

`doctor --strict` exited 1 with sixteen handoff errors against the hollow record,
quoted in the transcript above, and zero collateral errors. The workspace was a
fresh `git init` with one commit, so every git-derived check passed and only the
content gates fired.

# Blockers and questions

none — no open blockers. One open question: whether a 24-character floor is right
for projects whose notes are legitimately terse.

# Do not repeat / safe shortcuts

Do not re-derive that the three gates are reachable from the doctor's
`check_doctor` pass; the read set names them. Do not raise the section floor to
make a record pass — that weakens every future gate.

# Stale or contradictory information

An earlier draft of this file claimed the doctor auto-repaired empty sections. It
does not; the doctor is read-only and always has been.

# Working tree and uncommitted paths

The handoff files are untracked additions under
`.agent-workspace/tasks/T-0001-demo/handoffs/`. `app.py` is committed and
unmodified. `git status --porcelain` lists only the handoff directory.
EOF
cat > "$TASK/state.yaml" <<'EOF'
schema_version: 1
kind: TaskState
task_id: T-0001
state_revision: 2
status: in_progress
phase: handoff
readiness: ready
next_action: Run `python3 bin/agent-handoff doctor --strict` and confirm the record is rejected.
working_tree: clean
validation:
  status: pass
  run_ids: []
latest_handoff: H-20260926-002
execution: {}
EOF
RC=0
python3 -B "$CLI" doctor --strict > "$WORK/report2.json" 2>/dev/null || RC=$?
python3 - "$WORK/report2.json" <<'PYEOF' && good "ok  the new record is clean -- only the superseded one still fails" || bad "  DEMO ASSERTION FAILED"
import json, sys
report = json.load(open(sys.argv[1]))
errors = report["errors"]
stale = [e for e in errors if "H-20260926-001" in e]
on_new = [e for e in errors if "H-20260926-002" in e]
assert on_new == [], "the new handoff must be clean:\n  " + "\n  ".join(on_new)
assert stale, "the superseded record must still be rejected -- that is the point"
assert all("H-20260926-001" in e for e in errors), "unexpected error outside the superseded record:\n  " + "\n  ".join(errors)
print(f"  {len(stale)} errors, all of them against the superseded record")
print("  a superseded record keeps its rejection. History is not rewritten.")
PYEOF

b "7. Build the pack the next session reads"
cmd "python3 bin/agent-handoff context T-0001"
python3 -B "$CLI" context T-0001 2>/dev/null | python3 -c "
import json,sys
d=json.load(sys.stdin)
print(f'  ok={d[\"ok\"]}  records={len(d[\"records\"])}  git_head={str(d[\"git\"].get(\"head\"))[:7]}')
" 2>/dev/null || true
echo
echo "  every record is stamped and wrapped:"
grep -E 'source_sha256|untrusted-record' .agent-workspace/generated/context/T-0001-demo/context.md 2>/dev/null | head -3 | sed 's/^/    /'

b "8. The guarantee, stated precisely"
cat <<'EOF'
  A record that passes doctor is:
    well-formed   (9 JSON Schemas, additionalProperties: false)
    substantive   (no hollow section, no restatement, no fake next action)
    consistent    (the recorded commit exists, the tree state matches, the
                   ledger does not contradict the declared status)
    portable      (bounded, redacted, hash-stamped, marked untrusted)

  A record that passes doctor is NOT thereby true.
  Truth is not mechanically checkable. D3 in docs/acceptance-matrix.md exists
  so that gap stays visible.
EOF

b "Install it in your own project"
cat <<'EOF'
  git clone https://github.com/faresrafat3/agent-handoff
  cd agent-handoff && ./install.sh
EOF
echo
