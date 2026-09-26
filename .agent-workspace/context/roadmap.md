# Roadmap

Ordered by what unblocks the most value, not by what is most interesting to
build.

## Now

1. **A worked example end to end.** A `docs/EXAMPLE.md` that takes one real
   session from "context is full" to a fresh session with a valid pack. The
   README proves the pieces; nobody has seen them work in sequence.
2. **CI on this repository.** Run the suite and `doctor --strict` on every push.
   The self-hosting invariant is only trustworthy if it is checked
   automatically rather than remembered.
3. **`init --from-markdown`.** Migrate an existing convention onto the standard
   without hand-writing records. Adoption is the only bottleneck; every manual
   step is a project that does not adopt.

## Next

4. **A CI action.** `uses: faresrafat3/agent-handoff` to fail a build when a
   handoff goes stale. The check is worthless if a human has to remember to run
   it, and nobody remembers.
5. **Monorepo fixtures.** `--layout monorepo` is tested but undocumented. Real
   monorepo layouts are where the scope-graph gates earn their keep, so they
   deserve worked examples.
6. **Editor integration.** A command that writes the pack to the clipboard or
   opens it in a buffer, so the resume loop is one keypress rather than a
   copy-paste from a terminal.

## Deliberately not planned

- **Semantic judgement inside a gate** (D3). Needs a model, and a gate that
  needs a model cannot be falsified. It stays outside the tool, stated as a
  limitation in the acceptance matrix.
- **Automatic archiving** (D1, D2). "Abandoned" has no safe false-positive rate
  when a wrong guess destroys a closed task's only record.
- **A hosted service or dashboard.** The tool is vendored so a project's records
  outlive this repository. A hosted component inverts that.
- **Runtime dependencies.** Ever. See `WORKSPACE.md`.

## The open question blocking item 1

Whether `HANDOFF_MIN_BODY` should be fixed at 24 characters or configurable per
project. Fixed is simpler and language-stable; configurable suits projects with
shorter conventions. Default is fixed, because a configurable floor is a floor
nobody checks.
