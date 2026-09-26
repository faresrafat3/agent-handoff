# Product context

## The outcome

An engineer running a coding agent past its useful context can end the session
and start a new one without losing the thread — and can prove the handoff was not
hollow, was not stale, and did not contain a secret.

## Who it is for

Engineers and small teams who run coding agents for hours at a time on real
codebases, and who have lost work to context loss at least once. The secondary
audience is anyone whose agent runs unattended and must be resumable by a process
that did not watch it happen.

## Non-goals

- Not a durable-execution framework. `docs/landscape.md` says when to use
  Temporal, LangGraph, or the Agents SDK instead.
- Not semantic memory. It stores what it is told to store, in a checkable shape.
- Not an agent runtime, and not a workflow engine. It never runs the agent.
- Not a correctness oracle. A record that passes `doctor` is well-formed and
  consistent with git. It is not thereby true, and D3 in the acceptance matrix
  exists to keep that gap explicit.

## The distribution model

`git clone` and run `install.sh`. No account, no hosted component, no telemetry,
no network call. The tool is vendored into the target project so a project's
records stay readable years later without this repository existing.

## The honest summary

The value is not the file format. It is that a claim made by an agent about
work it just did can be **checked by something that did not watch it happen**.
That is a small idea with a narrow guarantee, and the guarantee is worth more
than a broader promise nobody can keep.
