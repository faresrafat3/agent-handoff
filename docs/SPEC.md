# Workspace Continuity Standard — Specification

**Version 1.0 · normative · MIT**

This document defines a standard, not a product. It is written so that an
implementation in any language can conform without reading the reference
implementation's source. The reference implementation is `agent-handoff`; it is
one of possibly many.

Conformance is decided by the published suite:

```sh
agent-handoff conformance        # 10 cases, fixed, each states why it exists
```

An implementation conforms when it produces the same accept/reject verdict on
every case. The cases are the definition. Where this prose and the suite
disagree, the suite is what gets tested — and the disagreement is a bug in one
of them, to be filed.

---

## 1. Purpose and scope

### 1.1 What this solves

A coding agent's working context is finite. When it fills, the usual response
is to summarize and continue. That response fails in four ways, and **all four
are silent** — a human reader cannot detect them by looking:

| # | Failure | Why it is silent |
|---|---|---|
| F1 | The record has required sections with no content under them | Structurally complete; passes every linter |
| F2 | The record's next action names nothing runnable | Reads as an instruction; executes as nothing |
| F3 | Two sections restate each other | Each passes a per-section check; jointly add nothing |
| F4 | The recorded checkpoint no longer matches the repository | A plausible-looking claim about a state that has moved on |

A summary cannot prevent any of these, because a summary is prose and prose
does not fail a build.

### 1.2 What this standard requires

A **typed record**, validated by **something that did not write it**, whose
failure is **mechanically detectable**.

### 1.3 Out of scope

Durable execution, workflow orchestration, semantic memory, and agent runtimes.
An implementation of this standard must not provide them, and must not claim to.
For what to reach for instead, see a landscape comparison in the reference
implementation's `docs/landscape.md`.

### 1.4 The central constraint

> **The verifier must be independent of the writer.**

An implementation MUST NOT delegate any conformance decision to a language
model. A verifier that shares a failure mode with the thing it verifies cannot
detect that failure mode. This is not a maturity preference; it is the reason
the standard exists.

A conforming implementation therefore has **zero model calls** in its gate, and
its gate MUST run with no network access.

---

## 2. Vocabulary

**Record** — a file holding a handoff, conforming to §4.
**Claim** — an assertion in a record about the world (a commit, a file state, a
completed step).
**Gate** — a check that MUST cause a non-zero exit on violation. A check that
only reports is a warning and MUST NOT be described as a gate.
**Workspace** — a directory containing `.agent-workspace/` (§3).
**Zone** — a named subtree of the workspace with fixed mutability rules (§3.3).
**Superseded record** — a record replaced by a later one, retained on disk.
**Conformance suite** — the fixed case list in §7.

---

## 3. Layout

### 3.1 Required paths

A workspace MUST contain all of:

```text
.agent-workspace/
  workspace.yaml            # manifest
  validation.yaml           # what a task may run
  schema/                   # the record contract
  tasks/
  decisions/
  research/
  generated/                # rebuildable projections
  scratch/                  # not evidence
  quarantine/               # failed validation, retained
  archive/                  # terminal history
```

An implementation MUST report each missing path individually. It MUST NOT
auto-create a missing path during a check, and it MUST NOT repair anything.

### 3.2 One home per fact

A fact MUST live in exactly one file. Every other surface MUST reference it by
id rather than restate it. Two copies of a fact is zero copies plus a conflict.

Record ids MUST be globally unique within the workspace and MUST match the
patterns in §4.2.

### 3.3 Zone mutability

| Zone | Mutability | Rule |
|---|---|---|
| `tasks/`, `decisions/`, `research/` | append; supersede | the record layer |
| `generated/` | freely rebuilt | derived; MUST NOT be cited as a source |
| `scratch/` | freely deleted | not evidence until promoted to a record |
| `quarantine/` | append only | retained so a failure stays inspectable |
| `archive/` | **never** | terminal history; see §6.4 |

### 3.4 A check is read-only

A conformance check MUST NOT create, modify, move, or delete any file. An
implementation MUST satisfy this for the suite in §7, and MUST be able to
demonstrate it.

Rationale: a tool that edits the records it is examining cannot be trusted to
have found a problem in them. Repair is a separate, explicit, human-invoked
action.

---

## 4. The record

### 4.1 Encoding

UTF-8. A record is a Markdown file with a YAML frontmatter block delimited by
`---` on its own line, followed by the body.

### 4.2 Frontmatter

Required fields, all of them, with no others:

| Field | Type | Constraint |
|---|---|---|
| `schema_version` | integer | MUST be `1` |
| `kind` | string | MUST be `Handoff` |
| `id` | string | `^H-[0-9]{8}-[0-9]{3}$` |
| `task_id` | string | `^T-[0-9]{4}$` |
| `session_id` | string | non-empty |
| `created_at` | string | ISO 8601 |
| `state_revision` | integer | ≥ 1 |
| `checkpoint.commit` | string or null | full SHA, or null |
| `checkpoint.tree_state` | enum | `clean` · `provisional-dirty` · `intentional-post-commit` |
| `checkpoint.validation_run_ids` | array of string | MAY be empty |
| `workspace.root` | string or null | absolute, or null |
| `workspace.git_head` | string or null | full SHA, or null |
| `workspace.branch` | string or null | |
| `workspace.dirty_paths` | array of string | |
| `objective` | string | ≥ 4 words after stripping non-alphanumerics |
| `next_action` | string | MUST satisfy §5.1 |
| `blockers` | array of string | MAY be empty |
| `sections` | array of string | ≥ 8 entries, all from §4.3 |

An unknown field MUST be a validation **error**, not a silently ignored key.
This is what makes a typo loud instead of invisible.

### 4.3 Required body sections

The body MUST contain these eleven level-one headings, in this order:

```text
# Objective and acceptance target
# Confirmed facts and read set
# Completed
# Current operation
# Exact next action
# Decisions/spec/plan changes
# Validation evidence
# Blockers and questions
# Do not repeat / safe shortcuts
# Stale or contradictory information
# Working tree and uncommitted paths
```

`sections` in the frontmatter MUST list at least eight of them, and every
heading it lists MUST be present in the body.

A section with no applicable content MUST be written `none — <reason>`. It MUST
NOT be left blank. Blanking it is failure F1.

### 4.4 The writer is named

The body MUST contain either the literal string `Source Session:` or a session
reference of the form `@[<session-id>]`.

Rationale: a record without an attributable writer cannot be correlated with
the session that made its claims, so a contradiction cannot be resolved.

---

## 5. Gates

Each gate below MUST produce a non-zero exit when violated, and MUST NOT produce
one otherwise. Gates MUST be independent: removing one MUST change the verdict on
at least one case in §7.

### 5.1 G-next-action — the next action must be runnable

A `next_action` MUST name at least one concrete target: a filesystem path, a
shell command, a record id (`T-NNNN`, `RES-NNNN`, `ADR-NNNN`, `RUN-…`, `H-…`),
or a backticked token.

It MUST be rejected when it is empty, or when it normalises to one of these
fourteen:

```text
carry on · continue · continue the work · do the thing · fix it · keep going · n/a · next · none · proceed · resume work · tbd · todo · work on it
```

An implementation MAY reject a longer denylist. The reference implementation
does: its `adopt` scanner carries 23 entries, adding `keep working`, `keep at
it`, `carry on from here`, `continue where we left off`, `resume`, `make it
work`, `finish the task`, `finish it`, and `continue where we left`. A
**conforming** implementation MUST reject the fourteen above; rejecting more is
permitted, rejecting fewer is not.

### 5.2 G-substantive — a section must carry information

A section body is checked after removing fenced code, inline markup, and URLs.
The remaining text MUST yield **at least six distinct alphabetic words of length
greater than two**.

Character counting is explicitly NOT sufficient and MUST NOT be used alone: it
accepts filler, a bare link, and eleven identical sentences.

### 5.3 G-independent — sections must not restate each other

No two sections in `sections` may share a Jaccard similarity above **0.6** over
their content word sets. Two sections that are paraphrases of one another
satisfy §5.2 individually while adding nothing jointly; that is failure F3.

### 5.4 G-checkpoint — the recorded commit must exist

If `checkpoint.commit` or `workspace.git_head` is a non-null string, that commit
MUST resolve in the repository.

**A shallow clone MUST be reported as shallow, not as a broken commit.** An
implementation MUST distinguish "this commit does not exist" from "this clone
cannot see far enough back to tell", and MUST NOT report the second as the
first. Conflating them trains users to ignore the gate.

### 5.5 G-tree-state — a dirty tree is provisional

`tree_state: clean` MUST NOT be claimed when `git status --porcelain` reports
changes, unless `dirty_paths` enumerates them. A dirty tree that has not captured
its diff MUST be `provisional-dirty`, which asserts the diff is recoverable
rather than assuming it.

### 5.6 G-credential — no credential may be in a record

A record MUST be rejected if it matches a credential pattern, including:
`sk-` followed by 12+ token characters, or `api_key` / `api-key` / `token` /
`password` followed by `:` or `=` and a value.

Redacting on output is NOT compliance. A credential in a record is a credential
in every context pack built from it, in every clone, and in git history. §7
case `C08` exists because a reference implementation once redacted on output and
did not refuse on input.

### 5.7 G-reference — every cited path and id must resolve

A path cited in a record MUST exist in the workspace. A cited record id MUST
resolve to a record. A handoff's filename MUST equal its frontmatter `id`.

### 5.8 G-attribution — a superseding record does not erase

When a newer record for a task exists, an earlier record MUST remain on disk and
MUST continue to be validated on its own terms. **A superseded record keeps its
verdict.** History is not rewritten because the newest record is good.

---

## 6. The context pack

### 6.1 A pack is a projection, not a record

`context` MUST emit a projection, and MUST NOT emit a transcript.

### 6.2 Required properties

| Property | Requirement |
|---|---|
| **Bounded** | A hard aggregate byte ceiling. Overflow MUST be marked `[TRUNCATED]`, never silently dropped |
| **Redacted** | Credential patterns stripped before emission |
| **Stamped** | Each record carries `source_sha256` (the file) and `emitted_sha256` (what was emitted) |
| **Untrusted** | Each record wrapped so a reading agent treats it as evidence, not instruction |
| **Contained** | A path that escapes the workspace, or is a symlink, MUST be refused |

### 6.3 Why "untrusted" is normative, not advisory

A context pack contains text that originated outside the current session. If
that text is emitted as instruction rather than as evidence, the pack becomes a
prompt-injection vector carrying the project's own notes into a new session.

An implementation that emits untrusted bytes MUST say so, in the pack and in the
resume prompt. A tool that moves the injection problem rather than closing it
has claimed a guarantee it does not have.

### 6.4 Archive is never ignored

An implementation MUST fail if the workspace's version-control ignore rules
exclude `archive/`. Archive is the only record of a closed task.

---

## 7. The conformance suite

Ten cases, fixed. **Eight MUST be rejected and two MUST be accepted**, and no
implementation may special-case them. The two `accept` cases are the minority on
purpose — see below.

| Case | Verdict | What it pins |
|---|---|---|
| `C01-hollow-section-rejected` | reject | §5.2 — a heading with no content |
| `C02-vague-next-action-rejected` | reject | §5.1 — "continue the work" |
| `C03-restated-sections-rejected` | reject | §5.3 — one section carrying another's words |
| `C04-thin-objective-rejected` | reject | §4.2 — a one-word objective |
| `C05-stale-commit-rejected` | reject | §5.4 — a commit that does not exist |
| `C06-unknown-frontmatter-rejected` | reject | §4.2 — an undeclared field |
| `C07-missing-section-rejected` | reject | §4.3 — a required heading absent |
| `C08-leaked-credential-rejected` | reject | §5.6 — a credential in a record |
| `C09-actionable-next-action-accepted` | **accept** | §5.1 must not reject real work |
| `C10-substantive-record-accepted` | **accept** | a complete record must pass |

The two `accept` cases are load-bearing, and they are a minority on purpose. A
suite of only rejections cannot distinguish a real gate from a blunt refusal that
rejects everything — and because a handoff tool's most natural failure mode is
being too strict, an unbalanced suite would certify exactly the wrong
implementations. **An implementation that rejects everything MUST NOT be reported
as conforming.**

---

## 8. The guarantee, stated exactly

A record that passes every gate is:

- **well-formed** — conforms to the schema, with no undeclared fields
- **substantive** — no hollow section, no restatement, no unrunnable next action
- **consistent** — its commit exists, its tree state matches, its cited paths and
  ids resolve, and it contains no credential
- **attributable** — its writer is named, and it is retained when superseded

A record that passes every gate is **NOT thereby true.**

Truth is not mechanically checkable. An implementation MUST NOT claim otherwise,
and MUST publish which of its intended gates are not yet enforced. The reference
implementation lists 26 closed gates and 5 deliberately deferred ones in
`docs/acceptance-matrix.md`, each deferred gate with the reason it is not
enforced. **A published list of what your implementation cannot do is part of
conforming.**

---

## 9. Conformance checklist

An implementation conforms when:

- [ ] All ten cases in §7 produce the specified verdict
- [ ] Gates run with no network access and no model calls
- [ ] Checks are read-only and demonstrably so (§3.4)
- [ ] Every gate is independent — removing it changes a §7 verdict
- [ ] Missing paths and missing workspace are reported separately, with an
      actionable next step
- [ ] A shallow clone is distinguished from a broken commit reference (§5.4)
- [ ] The list of intended-but-unenforced gates is published (§8)
- [ ] The tool has no runtime dependency, so it can be vendored and outlive its
      author

## 10. License

MIT. Implement this freely. The point of a standard is that people conform to it
without asking.
