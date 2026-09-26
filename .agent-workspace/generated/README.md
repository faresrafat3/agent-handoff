# generated/

Machine-built output. Never hand-edit anything in here.

| Path | What it is | Rebuildable |
|---|---|---|
| `context/<task>/context.md` | bounded, redacted, hash-stamped context pack for a fresh session | yes — `agent-handoff context <T-0001>` |

A context pack is a **projection**, not a record. The records it projects live
in `tasks/`, `decisions/`, and `research/`; this directory can be deleted
wholesale and rebuilt. Each pack carries `source_sha256` and `emitted_sha256`
per record so a reader can prove the projection was not edited after the fact.
