#!/usr/bin/env bash
# Usage: ./relay.sh <script.py>
# Encodes the python script, dispatches the ctf-relay workflow, waits, prints logs.
set -euo pipefail
REPO="ChandruMc0/CTF"
BRANCH="arena/01a0dc09-ctf"
WF="ctf-relay.yml"

SCRIPT_B64=$(base64 -w0 "$1")

# make sure workflow exists on branch from gh's perspective
gh workflow list --repo "$REPO" >/dev/null

gh workflow run "$WF" --repo "$REPO" --ref "$BRANCH" -f script="$SCRIPT_B64"
sleep 5

# find the run id (most recent for this workflow)
RUN_ID=""
for i in $(seq 1 20); do
  RUN_ID=$(gh run list --repo "$REPO" --workflow "$WF" --limit 5 --json databaseId,status,createdAt \
    | python3 -c "
import json,sys
runs=json.load(sys.stdin)
print(runs[0]['databaseId'] if runs else '')
")
  [ -n "$RUN_ID" ] && break
  sleep 3
done

echo "Run ID: $RUN_ID" >&2
gh run watch "$RUN_ID" --repo "$REPO" --exit-status --interval 5 >&2 || true
echo "=================== LOGS ==================="
gh run view "$RUN_ID" --repo "$REPO" --log 2>/dev/null | sed 's/^\s*[^ ]*\s//' || gh run view "$RUN_ID" --repo "$REPO" --log-failed
