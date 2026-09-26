#!/usr/bin/env bash
# Usage: ./relay.sh <script.py> [label]
# Copies the script to relay/cmd/<n>_<label>.py, pushes, waits for the run, prints logs.
set -euo pipefail
REPO="ChandruMc0/CTF"
BRANCH="arena/01a0dc09-ctf"

SRC="$1"
LABEL="${2:-cmd}"
mkdir -p relay/cmd
N=$(($(ls relay/cmd 2>/dev/null | sed 's/^0*//' | sort -n | tail -1) + 1))
N=$(printf "%03d" "${N:-1}")
DST="relay/cmd/${N}_${LABEL}.py"
cp "$SRC" "$DST"

git add "$DST"
if ! git diff --cached --quiet; then
  git commit -q -m "relay: run $LABEL"
  git push origin "$BRANCH" -q
else
  echo "nothing to commit" >&2
fi

sleep 8
RUN_ID=""
for i in $(seq 1 30); do
  RUN_ID=$(gh run list --repo "$REPO" --branch "$BRANCH" --workflow ctf-relay.yml --limit 1 \
    --json databaseId,headSha,status --jq '.[0].databaseId' 2>/dev/null || true)
  [ -n "$RUN_ID" ] && [ "$RUN_ID" != "null" ] && break
  sleep 4
done
echo "Run ID: $RUN_ID" >&2
if [ -z "$RUN_ID" ] || [ "$RUN_ID" = "null" ]; then
  echo "Could not find run" >&2; exit 1
fi
gh run watch "$RUN_ID" --repo "$REPO" --exit-status --interval 5 >/dev/null 2>&1 || true
echo "=================== LOGS ==================="
gh run view "$RUN_ID" --repo "$REPO" --log 2>/dev/null | sed 's/^\s*\S*\s*//' || gh run view "$RUN_ID" --repo "$REPO" --log-failed 2>/dev/null
