# Findings

All three claims below are read from the validator itself [S1] — the gate
names are locators, so every claim can be checked against code rather than
taken on trust. The gate names are the locator — read them, do not trust this
summary.

## C-1 — a hollow section is silent

A handoff with all eleven headings present and no content beneath any of them
looks complete to a human skimming for structure. It passes every markdown
linter. It tells the next session nothing.

Rejected by `section_is_substantive`, which requires a minimum body per section.
Test: `tests/test_handoff.py::SectionContentTests`.

## C-2 — a confident non-action is silent

"Exact next action: continue the work" reads as an action. It names no path, no
command, no id. A fresh session receiving it has nothing to execute and starts
guessing, which is how a settled decision gets reverted.

Rejected by `is_actionable`, which requires a path, command, task id, or
backticked token before it will accept an instruction. Test:
`tests/test_handoff.py::ActionableLanguageTests`.

## C-3 — a restated section is silent

Two sections carrying the same fact in different words satisfy a
presence-and-length check individually while adding no information jointly.
This is how hollow sections get padded rather than filled.

Rejected by `sections_are_independent`, which compares sections pairwise.
Test: `tests/test_handoff.py::SectionContentTests::test_restated_sections_are_detected`.

## What this record does not claim

It does not claim these are the only silent failure modes. It does not claim any
frequency or rate of occurrence. There is no dataset behind the word "observed"
other than this repository's own history, and a single-workspace sample is not
evidence about anyone else's agents.
