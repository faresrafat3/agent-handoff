# Acceptance matrix

What is enforced today, and what is deliberately **not** enforced yet.

A gate that is not listed as `CLOSED` does not run. Nothing here is
"almost working" — a gate is either enforced by a test that fails when the gate
is removed, or it is not a gate.

| # | Gate | State | Enforced by |
|---|---|---|---|
| G1 | Every record validates against its JSON Schema | `CLOSED` | `schema_validation` |
| G2 | Required body sections are present | `CLOSED` | `HANDOFF_HEADINGS` |
| G3 | A body section carries substance, not just a heading | `CLOSED` | `section_is_substantive` |
| G4 | Two sections do not restate each other | `CLOSED` | `sections_are_independent` |
| G5 | `next_action` names a path, command, id, or verification step | `CLOSED` | `is_actionable` |
| G6 | A recorded commit is a commit that exists | `CLOSED` | `git_commit_known` |
| G7 | A shallow clone is reported as shallow, not as a broken chain | `CLOSED` | `git_is_ancestor` |
| G8 | A context path cannot escape the workspace via `..` | `CLOSED` | `context` path check |
| G9 | A symlinked task, record, or context path is refused | `CLOSED` | symlink guards in `init` / `context` / `doctor` |
| G10 | Secrets are redacted before a context pack is emitted | `CLOSED` | `redact` + `SECRET_RE` |
| G11 | Emitted context is bounded by an aggregate byte ceiling | `CLOSED` | `context` truncation |
| G12 | Every emitted record carries `source_sha256` and `emitted_sha256` | `CLOSED` | `digest` / `digest_text` |
| G13 | The archive zone stays versioned | `CLOSED` | `.gitignore` policy check |
| G14 | Trust zones are git-ignored | `CLOSED` | `.gitignore` policy check |
| G15 | Research marked `verified` is not past its `review_by` | `CLOSED` | `check_doctor` staleness check |
| G16 | Every source in `sources.yaml` is cited from `notes.md` | `CLOSED` | `check_doctor` |
| G17 | Monorepo package scopes match the real manifests | `CLOSED` | `package_scope_errors` |
| G18 | Scope graph has no unknown, duplicate, or cyclic edges | `CLOSED` | `scope_graph_errors` |
| G19 | Ledger `fail` rows contradict a `pass` state | `CLOSED` | `check_doctor` |
| G20 | `adopt` writes nothing, anywhere | `CLOSED` | `test_adopt_is_read_only_and_creates_nothing` |
| G21 | `adopt` does not follow a symlink out of the tree | `CLOSED` | `test_adopt_does_not_follow_symlinks_out_of_the_tree` |
| G22 | `adopt` classifies a vague next action as vague, not merely as weak | `CLOSED` | `test_vague_next_action_is_classified_precisely` |
| G23 | `adopt` scans no more files than `--limit` | `CLOSED` | `test_scan_is_bounded_by_limit` |

## Deferred, and why

These are **not** implemented. They are listed so the gap is visible rather
than discovered by a user.

| # | Gate | State | Why it is not enforced yet |
|---|---|---|---|
| D1 | Automatic archiving of an abandoned task | `DEFERRED` | Needs a definition of "abandoned" that survives a wrong guess. A false positive destroys a closed task's only record. |
| D2 | Unattended task recycling | `DEFERRED` | Same failure mode as D1, with no human in the loop at all. |
| D3 | A handoff is semantically *correct*, not just well-formed | `DEFERRED` | Requires a model judgement inside a tool whose entire value is that it needs no model. Splitting it would make the guarantee unfalsifiable. |
| D4 | External-effect deduplication across sessions | `DEFERRED` | Needs a durable effect log, which is a different product (see `landscape.md`). |
| D5 | Authorization to resume a run unattended | `DEFERRED` | Safety-critical and needs a threat model, not a heuristic. |

## What this means in practice

A record that passes `doctor --strict` is **well-formed, internally consistent,
and consistent with git at the time it was checked.** It is not guaranteed to be
*true*. Nothing mechanical can promise that, and any tool implying otherwise is
selling a guarantee it does not have.
