# Contributing

## The gates are the contract

A change that **weakens a gate** needs a failing test first. Specifically, if
you want to make the doctor accept something it currently rejects, do not edit
the check — write the test that proves the rejection was wrong, then change the
check and cite the test in the commit body.

Raising a threshold to make your own record pass is the failure mode this
project exists to prevent. It will be rejected.

## Mutation testing is required for new gates

Every guard added to `bin/agent-handoff` must have a test that **fails when the
guard is deleted**. A guard whose absence the suite cannot detect is
decoration, and it will be treated as decoration.

```sh
# 1. confirm the suite is green
python3 -m unittest discover -s tests

# 2. delete or neuter the new guard

# 3. confirm the suite now FAILS
python3 -m unittest discover -s tests
```

If step 3 is still green, the new test does not actually test the new guard.
Fix the test before opening the pull request.

## Style

- Python 3.9+, standard library only. No runtime dependencies, ever. If a change
  needs a package, it belongs in a different project.
- The doctor is **read-only**. It reports; it never repairs, moves, or deletes.
  A tool that silently edits a user's records cannot be trusted to report on them.
- Prefer a bounded, deterministic check over a model call. Every gate here runs
  without a network, and that is a feature.
- Comments explain *why* a check exists, and usually name the failure that
  motivated it. A comment restating the code is noise.

## Before you open a pull request

```sh
./install.sh                                    # schemas + skill + verify
python3 -m unittest discover -s tests           # must be green
python3 bin/agent-handoff doctor --strict       # 0 errors on this repo
```

The third command runs against this repository, which uses its own standard on
itself. If it fails, the change broke the dogfooding invariant — that is a real
regression, not a test to be adjusted.

## Reporting a false positive

Open an issue with the exact handoff or record that was rejected and why you
believe the rejection was wrong. A reduced fixture is worth more than a
description. If the gate is wrong, the gate changes.
