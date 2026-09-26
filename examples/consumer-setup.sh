#!/usr/bin/env bash
# Vendor the standard into a project that has none. One command, no lockfile.
set -euo pipefail
git clone --depth 1 https://github.com/faresrafat3/agent-handoff
cd agent-handoff && ./install.sh
cd ..
# The tool now lives in .agent-workspace/ and runs with no network and no deps.
python3 -B .agent-workspace/bin/agent-handoff doctor --strict
echo
echo "next: add the CI gate from examples/ci-consumer.yml"
