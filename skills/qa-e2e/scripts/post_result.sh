#!/bin/zsh
# Post a QA comment on an issue, then set the issue's Status on the project board.
# Usage: post_result.sh <owner> <project-number> <repo owner/name> <issue> <status name|-> <comment.md>
#   status "-" posts the comment and leaves the status as it is.
# The comment file must have no "{{IMG:" placeholder left (run img_links.sh first).
set -e
OWNER=$1; PROJECT=$2; REPO=$3; N=$4; STATUS=$5; F=$6
[ -f "$F" ] || { echo "usage: $0 <owner> <project> <repo> <issue> <status|-> <comment.md>"; exit 1; }
grep -qF '{{IMG:' "$F" && { echo "unresolved image placeholder in $F"; exit 1; }
gh issue comment "$N" --repo "$REPO" --body-file "$F" >/dev/null
[ "$STATUS" = "-" ] && { echo "#$N commented, status unchanged"; exit 0; }
CACHE=${TMPDIR:-/tmp}/qa-e2e-ids-$OWNER-$PROJECT.json
if [ ! -s "$CACHE" ]; then
  PID=$(gh project view "$PROJECT" --owner "$OWNER" --format json -q .id)
  gh project field-list "$PROJECT" --owner "$OWNER" --format json \
    | jq --arg pid "$PID" '{pid:$pid, field:(.fields[]|select(.name=="Status"))}' > "$CACHE"
fi
PID=$(jq -r .pid "$CACHE"); FID=$(jq -r .field.id "$CACHE")
OPT=$(jq -r --arg s "$STATUS" '.field.options[]|select(.name==$s)|.id' "$CACHE")
[ -z "$OPT" ] && { echo "no Status option named \"$STATUS\""; exit 1; }
ITEM=$(gh api graphql -f query="{repository(owner:\"${REPO%%/*}\",name:\"${REPO##*/}\"){issue(number:$N){projectItems(first:20){nodes{id project{id}}}}}}" \
  | jq -r --arg pid "$PID" '.data.repository.issue.projectItems.nodes[]|select(.project.id==$pid)|.id')
[ -z "$ITEM" ] && { echo "#$N is not on the board"; exit 1; }
gh project item-edit --project-id "$PID" --id "$ITEM" --field-id "$FID" --single-select-option-id "$OPT" >/dev/null
echo "#$N commented, status -> $STATUS"
