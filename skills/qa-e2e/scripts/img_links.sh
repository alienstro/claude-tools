#!/bin/zsh
# Replace each {{IMG:<file>}} line in comment files with an <img> tag that points at the evidence branch.
# Usage: img_links.sh <repo owner/name> <branch> <folder in branch> <comment.md> [comment.md ...]
REPO=$1; BRANCH=$2; DIR=$3; shift 3
for f in "$@"; do
  BASE="https://github.com/$REPO/blob/$BRANCH/$DIR" perl -pi -e \
    's#\{\{IMG:([^}]+)\}\}#<img width="420" alt="$1" src="$ENV{BASE}/$1?raw=true">#g' "$f"
  grep -qF '{{IMG:' "$f" && echo "placeholder left in $f" || echo "ok $f"
done
