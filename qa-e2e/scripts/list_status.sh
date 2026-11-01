#!/bin/zsh
# List the issues in one status column of a GitHub Project board, with the PRs that link to each issue.
# Usage: list_status.sh <owner> <project-number> <repo owner/name> <out-dir> [status name, default "For Testing"]
# Writes <out-dir>/items.json (the whole board) and <out-dir>/column.tsv, and prints the TSV:
#   issue  state  labels  closer  linked-PRs(number:state:base)  title
set -e
OWNER=$1; PROJECT=$2; REPO=$3; OUT=$4; STATUS=${5:-For Testing}
[ -z "$OUT" ] && { echo "usage: $0 <owner> <project> <repo> <out-dir> [status]"; exit 1; }
mkdir -p "$OUT"
gh project item-list "$PROJECT" --owner "$OWNER" --format json --limit 1000 > "$OUT/items.json"
R_OWNER=${REPO%%/*}; R_NAME=${REPO##*/}
: > "$OUT/column.tsv"
for n in $(jq -r --arg s "$STATUS" --arg r "$REPO" '.items[] | select(.status==$s and .content.repository==$r) | .content.number' "$OUT/items.json"); do
  gh api graphql -f query="{repository(owner:\"$R_OWNER\",name:\"$R_NAME\"){issue(number:$n){number title state labels(first:6){nodes{name}} timelineItems(itemTypes:[CROSS_REFERENCED_EVENT,CLOSED_EVENT],first:30){nodes{__typename ... on ClosedEvent{closer{__typename ... on PullRequest{number} ... on Commit{oid}}} ... on CrossReferencedEvent{source{__typename ... on PullRequest{number state baseRefName}}}}}}}}" \
  | jq -r '.data.repository.issue | [
      (.number|tostring), .state,
      ([.labels.nodes[].name]|join(",")),
      ([.timelineItems.nodes[]|select(.__typename=="ClosedEvent")|.closer|if .==null then "none" elif .number then "PR\(.number)" else "commit:\(.oid[0:8])" end]|join(",")),
      ([.timelineItems.nodes[]|select(.__typename=="CrossReferencedEvent")|.source|select(.number)|"\(.number):\(.state):\(.baseRefName)"]|unique|join(",")),
      .title] | @tsv' >> "$OUT/column.tsv"
done
echo "$(wc -l < "$OUT/column.tsv" | tr -d ' ') issues in \"$STATUS\""
cat "$OUT/column.tsv"
