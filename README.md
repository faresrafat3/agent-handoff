# agent-handoff

**Your coding agent forgets everything between sessions. This makes that a test failure instead of a mystery.**

You are 4 hours into a refactor. Context is full. You start a new session to
finish it. The agent re-reads the code, "discovers" a decision you already made
two hours ago, and undoes your work. You find out 40 minutes later.

Everyone's fix is the same: *write a summary.* A summary cannot be validated. It
drifts. It silently becomes the only copy of a commit hash. Nothing catches it.

`agent-handoff` replaces the summary with a **typed, schema-checked handoff
document** that a validator rejects if it is hollow — and a `doctor` command that
tells you when a session's story no longer matches your git history.

Works with **Claude Code, Cursor, Codex, Cline, OpenCode, or any agent that can
run a shell command.** No harness. No daemon. No API key. Python 3 only.

---

## Install

```sh
git clone https://github.com/faresrafat3/agent-handoff
cd agent-handoff
./install.sh
```

Or use it without installing:

```sh
python3 bin/agent-handoff init        # create .agent-workspace/ in your project
python3 bin/agent-handoff doctor --strict
```

No dependencies. Nothing runs in the background. It only writes inside your
project.

---

## The problem, concretely

Three ways long agent sessions break. All three are silent.

**1. The confident non-action.** The agent writes:

```markdown
## Exact next action
Continue the work.
```

That is not an action. It names no file, no command, no test. A fresh session
receives it, has nothing to do, and starts guessing. `agent-handoff` rejects it:

```
$ agent-handoff doctor --strict
"Exact next action" is not actionable: it names no path, command, id, or verification step
```

**2. The hollow section.** Eleven headings, all present, all empty. It passes
every markdown linter ever written, and it tells the next session nothing.
`agent-handoff` rejects any section under 24 characters of substance, and
rejects two sections that are just restatements of each other.

**3. The stale claim.** The handoff says `git_head: a1b2c3d` and
`tree_state: clean`. You then commit `d4e5f6` with uncommitted changes. Now the
handoff is a lie and nothing knows. `agent-handoff doctor` re-reads git and
tells you the record is stale — because the claim is checkable, it is checked.

---

## What you get

| | |
|---|---|
| `agent-handoff init` | scaffolds `.agent-workspace/` — tasks, decisions, research, schemas |
| `agent-handoff doctor --strict` | **read-only** integrity report. 0 exit on clean, non-zero on any problem |
| `agent-handoff status` | what state every task is in |
| `agent-handoff context <T-0001>` | builds a **bounded, redacted, hash-stamped** context pack for a fresh session |
| `agent-handoff close <T-0001> --dry-run` | the checks to run *before* you call a task done |
| `skills/handoff/SKILL.md` | drop into Claude Code / Cursor / any agent so it writes conforming handoffs on its own |

The agent-facing workflow:

```text
/hand-off                      # agent writes a validated handoff, refuses to seal a hollow one
agent-handoff context T-0001   # you paste the generated pack into a fresh session
```

---

## Why the pack is not just a summary

`agent-handoff context` emits a **projection**, not a transcript:

- **Bounded** — a hard aggregate byte ceiling; overflow is marked `[TRUNCATED]`, never silently dropped.
- **Redacted** — API keys, tokens, and passwords are stripped before emission (`SECRET_RE`).
- **Stamped** — every record carries `source_sha256` *and* `emitted_sha256`, so you can prove the pack wasn't edited.
- **Untrusted** — every record is wrapped in `<untrusted-record>` so the reading agent treats it as evidence, not instruction. This blocks prompt injection through your own notes.
- **Escaped-path proof** — symlinked and `../` context paths are refused.

---

## It is tested, and the tests are the point

```sh
$ python3 -m unittest discover -s tests
Ran 67 tests
OK
```

Several guards are **mutation-tested**: delete one and the suite fails. That is
checked, not claimed — including four guards the suite originally failed to
notice, which were found and fixed rather than left as decoration.

Every gate here exists because an earlier version was caught accepting a bad
record. The empty-section check, the vague-next-action check, and the
independent-sections check were each added in response to a real hollow handoff
getting through.

---

## Honest limits

- It does **not** run your agent, schedule anything, or checkpoint a workflow. For durable execution use LangGraph, Temporal, OpenAI Agents SDK, or Google ADK. This sits one layer above them.
- It does **not** have semantic memory. It does not decide what is worth remembering.
- Archiving and task recycling stay **manual**. Five real gates are still `DEFERRED` and are listed in [`docs/acceptance-matrix.md`](docs/acceptance-matrix.md) rather than quietly marked done.
- The doctor is conservative by design: it reports, it never auto-fixes or deletes your data.

I'd rather ship five honest gates than twenty-five that don't hold.

---

## Why this exists

Built after losing real work to real context rot, then hardened against a
multi-agent research setup where a bad handoff silently corrupted a study. The
methodology — *records over claims, verify before claiming, generated counts
never hand counts* — is documented in [`docs/STANDARD.md`](docs/STANDARD.md).

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md). Gates are the contract; a change that
weakens a gate needs a failing test first.

## License

MIT
