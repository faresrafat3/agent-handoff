# Glossary

**Handoff** — a typed, schema-validated record transferring work from a finished
session to a fresh one. Not a summary: it is rejected when hollow.

**Hollow section** — a required heading present with no substance beneath it.
Looks complete to a human skimming for structure. Rejected by
`section_is_substantive`.

**Confident non-action** — a `next_action` that reads as an instruction but
names no path, command, id, or verification step. Rejected by `is_actionable`.

**Restatement** — two sections carrying the same fact in different words. Passes
a per-section check, adds nothing jointly. Rejected by
`sections_are_independent`.

**Checkpoint** — the recorded commit, tree state, and validation run ids a handoff
claims. Checkable against git, so it is checked. A dirty tree is
`provisional-dirty`, which claims the diff is captured and recoverable rather
than assuming it.

**Context pack** — a bounded, redacted, hash-stamped projection of a task's
records for a fresh session. Every record is wrapped as untrusted, which is the
prompt-injection defence.

**Projection** — derived, rebuildable output. A context pack is a projection. It
is never cited as a source; the records it projects are.

**Trust zone** — `generated/`, `scratch/`, `quarantine/`. Not evidence. Git-
ignored, except for a versioned README in each.

**Terminal history** — `archive/`. The only record of a closed task. Never
mutated, never git-ignored; violating that fails the build.

**Gate** — a check that fails the build. A check that reports is a warning. A
gate you weakened is a gate that no longer works.

**Mutation test** — deleting a guard must make the suite fail. A guard whose
absence the suite cannot detect is decoration, and is treated as decoration.

**The standard** — the Workspace Continuity Standard: layout, invariants, and
record rules. Normative text in `docs/STANDARD.md`.

**DSH** — DeepSeek Harness, the author's private agent host. `agent-handoff` has
**no** dependency on it and is not affiliated with it. See
`continuum-system` for the harness-integrated variant.
