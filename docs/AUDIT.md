# Is your agent setup actually verifiable?

A free diagnostic. It takes about thirty seconds and it writes nothing.

```sh
git clone https://github.com/faresrafat3/agent-handoff
cd agent-handoff && ./install.sh
python3 bin/agent-handoff adopt          # read-only
```

`adopt` scans the markdown notes you already keep and reports four things it can
determine without a model:

| Finding | What it means |
|---|---|
| `hollow-section` | A heading like *Current Status* or *Next Steps* with nothing under it. Looks complete; carries nothing. |
| `vague-next-action` | *continue the work*, *finish it*, *next steps* — no path, no command, no id, nothing runnable. |
| `unknown-commit` | The record cites a commit that is not in your repository. It is describing a world that has moved on. |
| `secret-pattern` | A credential in plain text in a note — which lands in git, in every clone, and in every context pack built from it. |

It prints a count per kind and a `fix` for each finding. It creates, moves, and
deletes nothing, and it never calls a model.

---

## Read this part before you decide anything

**If `adopt` reports zero findings, you do not need anything I sell.** That
outcome is common, and it is the correct answer for a lot of teams. Close this
tab.

If it reports findings, you now have a number instead of a promise. That number
is the whole conversation.

---

## What the number does not tell you

It cannot tell you whether your agent is producing the *right* answer. Nothing
mechanical can, and any vendor who says otherwise is selling a guarantee they do
not have. That limit is documented as gate **D3** in
[`acceptance-matrix.md`](acceptance-matrix.md) rather than hidden, because a tool
that implies more than it can do is worse than no tool.

What a finding *does* mean is narrow and checkable: **something you are relying
on is not true right now, and nothing in your current loop would have told you.**

---

## If the number is not zero

That is a solvable engineering problem, not a rewrite. In rough order of what
usually moves the number most:

1. **The next actions.** Most of the count is usually this. It is also the
   cheapest: name a path, a command, or the check that closes the work.
2. **The checkpoints.** Re-record from `git rev-parse HEAD` rather than from
   memory. Minutes of work, and it stops the record from describing a state that
   has moved on.
3. **The secrets.** Rotate, then remove. A redaction at output time is not a fix
   — the value is still in the file, in git, and in every clone.
4. **The hollow headings.** Either fill them or delete them. A heading with
   nothing under it is worse than no heading, because it reads as coverage.

Most teams that run this find that steps 1 and 2 clear most of it in an
afternoon, without adopting any tool at all. That is a perfectly good outcome
and I would rather it happened than not.

---

## If you want it handled rather than diagnosed

I do a fixed-scope, one-week **Agent Reliability Audit**. Same analysis, then the
fixes, wired in.

- **$1,800** — one agent pipeline
- **$4,500** — up to three pipelines, or one plus the regression harness in CI

You get a failure-mode map, a working regression suite in your repo, a
prioritized plan, and a recorded walkthrough. 50% up front.

**About a third of audits end with me telling you the real problem is somewhere
else**, and referring you on. That is a real outcome, not a sales tactic.

Start here: [faresrafat3@gmail.com](mailto:faresrafat3@gmail.com) with the repo
URL and a 30-minute slot. I will tell you within two days whether this is the
right thing or whether you do not need it at all.

---

## Why the free part is genuinely free

The tool is MIT, single-file, dependency-free, and vendored into your repo. It
has no account, no telemetry, and no network call in any gate.

I would rather a hundred teams run the diagnostic and fifty of them conclude
they are fine than have one team pay for a fix they do not need. The diagnostic
is also the first day of the audit, so the paid work starts from a number rather
than from a pitch.
