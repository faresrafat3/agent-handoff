# quarantine/

Records that failed validation and were moved here rather than deleted or
silently repaired.

Nothing in this directory is trusted, and nothing in it is read by
`agent-handoff context` — quarantined material is excluded from context packs
by design. A quarantined record is kept for one reason: so the failure that
moved it there stays inspectable after the fact.

This file is versioned; the contents are not.
