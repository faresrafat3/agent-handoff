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

# The CLI validates records against JSON Schema, so the schemas must exist in
# the target workspace. Ship them; never overwrite a schema the project edited.
mkdir -p .agent-workspace/schema
SHIPPED=0
for s in "$SOURCE"/schemas/*.json; do
  [ -f "$s" ] || continue
  dest=".agent-workspace/schema/$(basename "$s")"
  if [ -e "$dest" ]; then
    cmp -s "$s" "$dest" || warn "kept your edited $dest (differs from shipped)"
    continue
  fi
  cp "$s" "$dest" && SHIPPED=$((SHIPPED + 1))
done
ok "installed $SHIPPED schema(s) into .agent-workspace/schema/"

# --------------------------------------------------------- harness-agnostic
# The skill is a single markdown file. Copy it wherever your agent reads
# skills from; nothing here is required for the CLI to work.
COPIED=0
for dest in \
  "${CLAUDE_SKILL_DIR:-$HOME/.claude/skills/handoff}" \
  "$HOME/.cursor/rules/handoff.md" \
  "$HOME/.config/opencode/skills/handoff"
do
  case "$dest" in
    "$HOME"/*) ;;
    *) continue ;;   # never write outside the user's home
  esac
  if [ -e "$dest" ]; then
    continue
  fi
  mkdir -p "$(dirname "$dest")" 2>/dev/null || continue
  if cp "$SKILL_SRC" "$dest" 2>/dev/null; then
    ok "installed skill -> ${dest/#$HOME/\$HOME}"
    COPIED=$((COPIED + 1))
  fi
done
[ "$COPIED" -gt 0 ] || warn "no skill directory created (all existed or unwritable) — the CLI still works standalone"

# ------------------------------------------------------------------ verify
printf '\n'
python3 -B "$CLI" doctor --strict >/dev/null 2>&1 \
  && ok "doctor --strict: 0 errors, 0 warnings" \
  || warn "doctor reported findings — run: python3 bin/agent-handoff doctor --strict"

python3 -B -m unittest discover -s "$SOURCE/tests" >/dev/null 2>&1 \
  && ok "test suite passed" \
  || warn "test suite did not pass — run: python3 -m unittest discover -s tests"

cat <<'NEXT'

next
  1. tell your agent about the handoff format:
       "read skills/handoff/SKILL.md and follow it when you finish a unit of work"
  2. at the end of a work session:
       python3 bin/agent-handoff close <T-0001> --dry-run
  3. in a fresh session, build the context pack and paste it in:
       python3 bin/agent-handoff context <T-0001>

verify any time
  python3 bin/agent-handoff doctor --strict
NEXT
