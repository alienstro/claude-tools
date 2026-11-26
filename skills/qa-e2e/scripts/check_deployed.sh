#!/bin/zsh
# Tell, for each PR, whether its merge commit is inside the build that the test environment runs.
# Usage: check_deployed.sh <repo owner/name> <deployed commit sha> <pr> [pr ...]
# Run it inside a clone of the repository, after `git fetch`.
REPO=$1; SHA=$2; shift 2
[ -z "$SHA" ] && { echo "usage: $0 <repo> <deployed-sha> <pr>..."; exit 1; }
git cat-file -e "$SHA" 2>/dev/null || { echo "commit $SHA is not in this clone; run git fetch"; exit 1; }
for p in "$@"; do
  c=$(gh pr view "$p" --repo "$REPO" --json mergeCommit,state -q '"\(.state) \(.mergeCommit.oid // "")"')
  st=${c%% *}; oid=${c#* }
  if [ "$st" != "MERGED" ] || [ -z "$oid" ]; then echo "#$p $st not-merged"; continue; fi
  if git merge-base --is-ancestor "$oid" "$SHA" 2>/dev/null; then echo "#$p ${oid:0:8} deployed"; else echo "#$p ${oid:0:8} NOT-deployed"; fi
done
