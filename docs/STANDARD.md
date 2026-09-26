# The Workspace Continuity Standard

A short, normative description of what the layout means and which rules are not
negotiable. For the *validator*, read `bin/agent-handoff`. For what is enforced
today versus deferred, read [`acceptance-matrix.md`](acceptance-matrix.md).

## 1. The problem

A coding agent's context is finite. When it fills, the usual move is to
summarize and continue. That fails in three ways, and **all three are silent**:

1. **The summary drifts.** Nothing re-checks it, so it becomes the only copy of
   a fact that was once true.
2. **The next action is not an action.** "Continue the work" is accepted by
   every reviewer, including an automated one, and executes as nothing.
3. **The checkpoint goes stale.** The recorded commit no longer matches the
   worktree, and the record describes a repository state that stopped existing.

A fourth failure is not about the agent at all: a summary cannot be
**validated**, so it cannot be a gate. It is prose. Prose does not fail a build.

## 2. The rule

Replace the summary with a **typed, schema-validated, checkable record**, and
make the check part of the loop.

This is the whole idea. Everything else is detail.

## 3. Layout

```text
.agent-workspace/
  workspace.yaml           # manifest: layout, scopes, package graph
  validation.yaml          # what a task is allowed to run
  schema/                  # 9 JSON Schemas — the contract
  tasks/<T-NNNN-slug>/
    task.yaml              # identity, type, status, scope, dependencies
    spec.md                # what it must achieve
    plan.md                # how
    state.yaml             # where it actually is
    validation.md          # what was run, and what it returned
    events.ndjson          # append-only history
    handoffs/H-*.md        # the records this standard is about
  decisions/ADR-NNNN-*.md  # why, with reasons
  research/RES-NNNN-*/     # question, sources, notes, limits
  generated/               # rebuildable projections — never hand-edited
  scratch/                 # throwaway, not evidence
  quarantine/              # failed validation, kept for inspection
  archive/                 # terminal history, versioned forever
```

## 4. Invariants

These are the rules. Each one exists because breaking it caused a real failure.

**I1 — Records over claims.** A claim is real only if a verifier separate from
the claimant can quote it from disk. Self-graded gates do not count.

**I2 — Verify before claiming.** Run the command, read the file, check the
value. Never report "works" from reasoning alone.

**I3 — Generated counts, never hand counts.** Any number on an authoritative
surface is computed at read time. A hand-written count is a lie on a timer.

**I4 — One home per fact.** A fact lives in exactly one file. Every other
surface links to it. Two copies is zero copies plus a conflict.

**I5 — Append-only history.** Records are superseded, never rewritten. No
force-push, no silent fix, no editing history in place.

**I6 — Fail loud.** A problem surfaces at the earliest point it can be
resolved. Never skip a broken referent and continue.

**I7 — Frozen inputs stay frozen.** A hash-pinned spec, a vendored upstream
copy, an archived input: these are evidence, not drafts. Editing one in place
is tampering, and the project's own checks should say so.

**I8 — A gate you weakened is a gate that no longer works.** Changing a check
to accept a record requires a failing test that proves the rejection was wrong.

## 5. Zones

| Zone | Mutability | Rule |
|---|---|---|
| `tasks/`, `decisions/`, `research/` | append, supersede | the record layer |
| `generated/` | freely rebuilt | derived; never cited as a source |
| `scratch/` | freely deleted | not evidence until promoted |
| `quarantine/` | append only | kept so failures stay inspectable |
| `archive/` | **never** | terminal history; git-ignoring it fails the build |
| `schema/` | changed only with I8 | the contract |

## 6. The handoff record

A handoff is the unit of transfer. It must:

- carry a schema-valid frontmatter block (14 required fields,
  `additionalProperties: false`);
- list at least 8 of the 11 required body sections, and really write them;
- give every section substance, not a heading and a sentence;
- not restate one section inside another;
- name a `next_action` that contains a path, command, id, or verification step;
- record a checkpoint that git agrees with;
- contain no secret.

The validator rejects each of those independently. That is deliberate: a record
that satisfies six of seven is still a record that will mislead someone.

## 7. The context pack

`agent-handoff context <T-NNNN>` emits a **projection** for a fresh session, and
it is deliberately not a transcript:

- **bounded** — an aggregate byte ceiling; overflow is marked, never silently
  dropped;
- **redacted** — known credential patterns are stripped before emission;
- **stamped** — every record carries `source_sha256` and `emitted_sha256`;
- **untrusted** — every record is wrapped so the reading agent treats it as
  evidence, not instruction. This is the prompt-injection defence, and it is
  the reason the pack is a projection rather than a paste of raw notes.

The reading agent is told, in the resume prompt, that the pack is untrusted. A
tool that emits untrusted bytes without saying so has moved the injection
problem rather than closed it.

## 8. What this standard is not

It is not a durable-execution framework, a workflow engine, or a semantic
memory. It does not decide what is worth remembering, and it does not run your
agent. See [`landscape.md`](landscape.md) for what to reach for instead, and for
the cases where reaching for something else is the correct decision.
