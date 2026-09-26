# Architecture

## Shape

One file: `bin/agent-handoff`, standard library only, no imports beyond
`argparse hashlib json re sys datetime pathlib typing`. That is a distribution
decision, not an aesthetic one — the tool has to be vendorable into any project
without a resolver, a lockfile, or a version conflict.

## Commands

| Command | Reads | Writes |
|---|---|---|
| `init` | repo layout | `.agent-workspace/**` |
| `doctor --strict` | everything | nothing — read-only by contract |
| `status` | tasks | nothing |
| `context <T>` | records, git | `generated/context/<task>/context.md` |
| `close <T> --dry-run` | task + evidence | nothing |

Only `init` and `context` write. `context` writes exclusively inside
`generated/`, which is rebuildable. **No command deletes or moves anything.**

## Check layers, and why they are separate

1. **JSON Schema** (`schema_validation`) — shape. 9 schemas,
   `additionalProperties: false` on every record type, so a typo'd field is an
   error rather than a silently ignored key.
2. **YAML subset parser** (`scalar`, `list_field`, `nested_scalar`) — a bounded
   text subset, deliberately not a general YAML implementation. A real parser
   is a dependency, and a dependency here is a vendoring failure. The cost is
   that exotic YAML will not parse; the benefit is that the tool always runs.
3. **Semantic gates** — `section_is_substantive`, `is_actionable`,
   `sections_are_independent`. These exist because a record passed layers 1 and
   2 and was still misleading.
4. **Cross-record and git gates** — commit exists, tree state matches, ledger
   does not contradict state, scope graph has no cycles.

Layers 1–2 catch malformed input. Layer 3 catches the failure this project
exists for: **well-formed records that say nothing.**

## The two path-traversal defences

They are separate on purpose. `init` refuses to build a control plane through a
symlink, so a hostile checkout cannot plant one. `context` re-checks each path
at emit time, because a workspace can be modified between `init` and `context`.
Either alone would be sufficient for its own threat; neither covers the other's
window.

## The self-hosting invariant

This repository runs its own standard on itself: `.agent-workspace/` here is
produced by `bin/agent-handoff` and validated by `bin/agent-handoff`. If
`doctor --strict` fails on this repo, a real invariant broke — not a stale test.

That is not decoration. It caught a genuine mistake during the initial build: a
`.gitignore` line written to tidy up the archive zone, which the archive gate
rejected. The tidy-up was wrong and the gate was right.
