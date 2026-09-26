#!/usr/bin/env bash
# agent-handoff installer — harness-agnostic, dependency-free.
#
# Writes only inside the target project, plus (optionally) one skill directory
# in your home. Refuses to run if the resolved target escapes the project root.
set -euo pipefail

VERSION="1.0"
SOURCE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLI="$SOURCE/bin/agent-handoff"
SKILL_SRC="$SOURCE/skills/handoff/SKILL.md"

bold() { printf '\033[1m%s\033[0m\n' "$1"; }
ok()   { printf '  \033[32mok\033[0m    %s\n' "$1"; }
warn() { printf '  \033[33mwarn\033[0m  %s\n' "$1"; }
die()  { printf '  \033[31mfail\033[0m  %s\n' "$1" >&2; exit 1; }

bold "agent-handoff installer"
printf '  source     %s\n' "$SOURCE"
printf '  target     %s\n' "$(pwd)"
printf '  version    %s\n\n' "$VERSION"

# ---------------------------------------------------------------- preflight
command -v python3 >/dev/null 2>&1 || die "python3 not found. Python 3.9+ is required."
PY_OK="$(python3 -c 'import sys; print(1 if sys.version_info >= (3, 9) else 0)')"
[ "$PY_OK" = "1" ] || die "python3 >= 3.9 required, found $(python3 -V 2>&1)"
ok "python3 $(python3 -V 2>&1 | cut -d' ' -f2)"

[ -x "$CLI" ] || die "missing or non-executable: $CLI"
[ -f "$SKILL_SRC" ] || die "missing skill: $SKILL_SRC"
ok "source tree complete"

# Refuse to run against a filesystem root or $HOME itself.
TARGET="$(pwd -P)"
[ "$TARGET" = "/" ] && die "refusing to install into /"
[ "$TARGET" = "$HOME" ] && die "refusing to install into \$HOME directly — use a project directory"

# ------------------------------------------------------------ workspace init
if [ -d .agent-workspace ]; then
  ok ".agent-workspace already exists — leaving it untouched (init never overwrites)"
else
  python3 -B "$CLI" init >/dev/null || die "init failed"
  ok "created .agent-workspace/"
fi

# Vendor the tool into the workspace. The standard promises a project can keep
# working after this repository is gone, which is only true if the tool travels
# with the project. The action's `vendor` input does the same thing; doing it
# here means a manual install is not a second-class installation.
mkdir -p .agent-workspace/bin
if [ -f .agent-workspace/bin/agent-handoff ] && cmp -s "$CLI" .agent-workspace/bin/agent-handoff; then
  ok "tool already vendored at .agent-workspace/bin/agent-handoff"
else
  cp "$CLI" .agent-workspace/bin/agent-handoff
  chmod +x .agent-workspace/bin/agent-handoff
  ok "vendored tool -> .agent-workspace/bin/agent-handoff (runs with no network, no deps)"
fi

# The CLI validates every record against JSON Schema, so a workspace without
# schemas is a broken workspace. `init` copies them out of this repo's own
# self-hosted .agent-workspace/schema/. Verify rather than assume.
SCHEMA_COUNT="$(find .agent-workspace/schema -name '*.json' 2>/dev/null | wc -l | tr -d ' ')"
if [ "$SCHEMA_COUNT" -ge 9 ]; then
  ok "schemas present in .agent-workspace/schema/ ($SCHEMA_COUNT)"
else
  for s in "$SOURCE"/schemas/*.json; do
    [ -f "$s" ] || continue
    mkdir -p .agent-workspace/schema
    cp -n "$s" ".agent-workspace/schema/$(basename "$s")" 2>/dev/null || true
  done
  RECOUNT="$(find .agent-workspace/schema -name '*.json' 2>/dev/null | wc -l | tr -d ' ')"
  [ "$RECOUNT" -ge 9 ] \
    && ok "schemas recovered from source tree ($RECOUNT)" \
    || die "only $RECOUNT/9 schemas present — copy $SOURCE/schemas/*.json into .agent-workspace/schema/"
fi

# --------------------------------------------------------- harness-agnostic
# The skill is a single markdown file. Copy it wherever your agent reads
# skills from; nothing here is required for the CLI to work.
# A skill is a directory containing SKILL.md for Claude Code and OpenCode, but
# a flat markdown file for Cursor rules. Getting this wrong installs a file
# where a directory is expected and the skill silently never loads.
COPIED=0
install_skill() {           # $1 = destination SKILL.md path
  local dest="$1"
  case "$dest" in
    "$HOME"/*) ;;
    *) return 0 ;;          # never write outside the user's home
  esac
  [ -e "$dest" ] && return 0
  mkdir -p "$(dirname "$dest")" 2>/dev/null || return 0
  cp "$SKILL_SRC" "$dest" 2>/dev/null || return 0
  ok "installed skill -> ${dest/#$HOME/\$HOME}"
  COPIED=$((COPIED + 1))
}

install_skill "$HOME/.claude/skills/handoff/SKILL.md"
install_skill "$HOME/.config/opencode/skills/handoff/SKILL.md"
install_skill "$HOME/.cursor/rules/handoff.md"

[ "$COPIED" -gt 0 ] || warn "no skill installed (all present or unwritable) — the CLI still works standalone"

# ------------------------------------------------------------------ verify
printf '\n'
python3 -B "$CLI" doctor --strict >/dev/null 2>&1 \
  && ok "doctor --strict: 0 errors, 0 warnings" \
  || warn "doctor reported findings — run: python3 bin/agent-handoff doctor --strict"

python3 -B -m unittest discover -s "$SOURCE/tests" >/dev/null 2>&1 \
  && ok "test suite passed" \
  || warn "test suite did not pass — run: python3 -m unittest discover -s tests"

cat <<'NEXT'

the tool now lives in your project
  .agent-workspace/bin/agent-handoff     <- yours; survives this repo

next
  0. check what is already hollow in your notes (read-only, writes nothing):
       python3 .agent-workspace/bin/agent-handoff adopt
  1. tell your agent about the handoff format:
       "read skills/handoff/SKILL.md and follow it when you finish a unit of work"
  2. at the end of a work session:
       python3 bin/agent-handoff close <T-0001> --dry-run
  3. in a fresh session, build the context pack and paste it in:
       python3 bin/agent-handoff context <T-0001>

verify any time
  python3 bin/agent-handoff doctor --strict
NEXT
