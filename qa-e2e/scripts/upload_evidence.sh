#!/bin/zsh
# Upload screenshots to an evidence branch, so that issue comments can embed them.
# Usage: upload_evidence.sh <repo owner/name> <branch> <folder in branch> <file> [file ...]
# Prints the embed URL of each file. The branch must exist already.
REPO=$1; BRANCH=$2; DIR=$3; shift 3
TMPJ=$(mktemp)
for f in "$@"; do
  b=$(basename "$f")
  printf '{"message":"qa evidence %s","branch":"%s","content":"%s"}' "$b" "$BRANCH" "$(base64 -i "$f" | tr -d '\n')" > "$TMPJ"
  if gh api -X PUT "repos/$REPO/contents/$DIR/$b" --input "$TMPJ" -q .content.path >/dev/null 2>&1; then
    echo "https://github.com/$REPO/blob/$BRANCH/$DIR/$b?raw=true"
  else
    echo "FAILED $b (a file with this name may exist; rename it)"
  fi
done
rm -f "$TMPJ"
