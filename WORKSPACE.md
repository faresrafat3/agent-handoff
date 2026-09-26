# Scope map

## What this repository is

One dependency-free Python CLI (`bin/agent-handoff`), one JSON Schema contract
(`schemas/`), and one agent-facing skill (`skills/handoff/SKILL.md`). It defines
a convention for ending an agent work session and validating what the next
session is told.

## Layout

| Path | Role |
|---|---|
| `bin/agent-handoff` | the entire tool. Single file, stdlib only. |
| `schemas/*.json` | the record contract. Shipped to user workspaces by `init`. |
| `skills/handoff/SKILL.md` | tells any agent to write conforming handoffs. |
| `install.sh` | provisions schemas + skill, then verifies. Idempotent. |
| `tests/` | 60 tests. Every guard has a test that fails when the guard is removed. |
| `docs/STANDARD.md` | the normative spec: invariants, zones, record rules. |
| `docs/acceptance-matrix.md` | what is `CLOSED` vs `DEFERRED`, and why. |
| `docs/landscape.md` | when to use something else instead. |
| `.agent-workspace/` | this repo's own workspace — the standard, self-hosted. |

## Boundaries — what is deliberately not here

- **No runtime dependency.** Never add one. A validator that needs a package
  cannot be vendored into a target project, and vendoring is the whole
  distribution model.
- **No network inside a gate.** Every check is deterministic and offline. If a
  check needs a judgement call, it belongs outside the tool.
- **No auto-repair.** The doctor reports. A tool that fixes your records cannot
  be trusted to have found the problem.
- **No semantic memory, no durable execution, no agent runtime.** See
  `docs/landscape.md`. Building any of these here would be a different product
  with a different threat model.
- **No hosted service.** There is no account, no telemetry, and no phone-home.
  A tool that reports on your repository does not get to also report to someone
  else.

## The one invariant that is easiest to break

`.agent-workspace/archive/` must stay versioned. It is the only record of a
closed task. `doctor` fails the build if it is ever git-ignored — a check that
has already caught one attempted "cleanup" in this repository's own history.
