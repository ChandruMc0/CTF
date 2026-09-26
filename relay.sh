#!/usr/bin/env bash
# Usage: ./relay.sh <script.py> [label]
# Pushes the script as relay/cmd/NNN_label.py; the ctf-relay workflow runs it and
# pushes output to the relay-out branch; this script polls and prints the output.
set -euo pipefail
REPO="ChandruMc0/CTF"
BRANCH="arena/01a0dc09-ctf"

SRC="$1"
LABEL="${2:-cmd}"
mkdir -p relay/cmd
LAST=$(ls relay/cmd 2>/dev/null | sed 's/^0*//' | cut -d_ -f1 | sort -n | tail -1)
LAST=${LAST:-0}
N=$(printf "%03d" $((LAST+1)))
BASE="${N}_${LABEL}"
DST="relay/cmd/${BASE}.py"
cp "$SRC" "$DST"

git add "$DST"
git commit -q -m "relay: $LABEL"
git push -q origin "$BRANCH"
echo "pushed $DST ; waiting for output..." >&2

for i in $(seq 1 150); do
  sleep 6
  if git fetch -q origin relay-out 2>/dev/null; then
    if git show "origin/relay-out:out/${BASE}.txt" > /tmp/relay_out.txt 2>/dev/null; then
      cat /tmp/relay_out.txt
      exit 0
    fi
  fi
done
echo "TIMEOUT waiting for output out/${BASE}.txt" >&2
exit 1
