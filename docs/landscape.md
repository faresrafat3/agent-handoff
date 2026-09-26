# Where this fits, and when not to use it

Written to be useful rather than flattering. If one of the alternatives below
solves your problem, use it.

## The category error

The most common misreading is to treat this as a competitor to LangGraph,
Temporal, the OpenAI Agents SDK, Google ADK, or AutoGen. It is not.

Those are **durable-execution and runtime frameworks**. They give you
checkpointing, replay, scheduling, and human-in-the-loop primitives. They do not
give you a convention for a workspace, a contract for a handoff document, or a
checker for either.

This standard is **one layer above them**: a convention and a validator for
deciding when a working session should end and how the next one is told what it
needs.

| | this | LangGraph / Temporal / ADK |
|---|---|---|
| Runs a workflow | no | yes |
| Checkpoints and replays | no | yes |
| Decides when to seal a session | yes | no |
| Types the handoff document | yes | no |
| Validates that document | yes | no |
| Bounded, redacted context projection | yes | no |
| Needs a server | no | usually |
| Maturity | new, self-audited | years, production |

They compose. Run your durable execution on Temporal; use this to decide what
the operator reads when the run is interrupted.

## Reach for something else when

**You need durable execution, replay, or scheduling.** Use Temporal, LangGraph,
Inbox, or Restate. This standard will not give you a resumable run, and D4 in
the acceptance matrix is the honest reason why.

**You need semantic memory — "remember that I prefer X."** Use a memory system.
This standard stores what you tell it to store, in a shape a validator can
check. That is a different guarantee and a different tool.

**Your agent framework already has a handoff format that works.** Use it. If
your framework ships a validated handoff contract, this adds a second dialect
and a migration for no gain. Read its contract first; if it already rejects
hollow sections, you are done.

**You have one session that ends cleanly.** You do not need this. The failure
modes here only appear when a session is interrupted, compacted, or handed to a
successor. A workflow that always completes in one pass does not need a
continuity standard.

**You need to know whether the agent was *right*.** This cannot tell you and
does not claim to. It tells you the record is well-formed, internally
consistent, and consistent with git. Truth is not mechanically checkable, and
D3 in the acceptance matrix exists to make that gap explicit rather than let a
reader assume it away.

## When it does pay

- Long sessions on a real codebase, where compaction happens more than once a day.
- Handoffs between people, where "I read the summary and guessed" is a
  recurring tax.
- Any workflow where an interrupted run must be resumable by something that did
  not watch it happen.
- A team that has been burned by a stale status document and now distrusts
  every status document.
