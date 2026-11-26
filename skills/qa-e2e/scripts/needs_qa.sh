#!/bin/zsh
# Tell, for each issue, if it needs a QA run: "untested", "retest" (a fix merged after the last verdict) or "tested".
# Usage: needs_qa.sh <repo owner/name> <issue> [issue ...]     Self-test: needs_qa.sh --self-test
# Only a "## QA result: PASS" or "FAIL" comment is a verdict; BLOCKED and NOT DEPLOYED runs need a new run.
# The fix date is the newest mergedAt of the linked PRs, or the issue's closedAt when no PR links to it.
FILTER='.data.repository.issue as $i | if $i == null then "#\(env.N) not-an-issue" else
  ([$i.comments.nodes[] | select(.body|test("^## QA result: (PASS|FAIL)";"m")) | .createdAt] | max) as $qa
  | ([$i.timelineItems.nodes[] | (.closer // .source // .subject // {}) | .mergedAt // empty] | max // $i.closedAt) as $fix
  | "#\($i.number) \(if $qa == null then "untested" elif $fix != null and $fix > $qa then "retest" else "tested" end) last-verdict=\($qa // "-") last-fix=\($fix // "-")" end'

if [ "$1" = "--self-test" ]; then
  t() { local got; got=$(echo "$2" | N=1 jq -r "$FILTER" | cut -d' ' -f2); [ "$got" = "$1" ] && echo "ok $1" || { echo "FAIL want $1 got $got"; return 1; }; }
  pr='{"__typename":"CrossReferencedEvent","source":{"mergedAt":"2026-01-05T00:00:00Z"}}'
  t untested '{"data":{"repository":{"issue":{"number":1,"closedAt":null,"comments":{"nodes":[{"createdAt":"2026-01-09T00:00:00Z","body":"## QA result: BLOCKED — x"}]},"timelineItems":{"nodes":['$pr']}}}}}' &&
  t tested '{"data":{"repository":{"issue":{"number":1,"closedAt":null,"comments":{"nodes":[{"createdAt":"2026-01-09T00:00:00Z","body":"## QA result: PASS — x"}]},"timelineItems":{"nodes":['$pr']}}}}}' &&
  t retest '{"data":{"repository":{"issue":{"number":1,"closedAt":null,"comments":{"nodes":[{"createdAt":"2026-01-01T00:00:00Z","body":"## QA result: FAIL — x"}]},"timelineItems":{"nodes":['$pr']}}}}}' &&
  t not-an-issue '{"data":{"repository":{"issue":null}}}'
  exit $?
fi

REPO=$1; shift
[ -z "$1" ] && { echo "usage: $0 <repo> <issue>..."; exit 1; }
for n in "$@"; do
  gh api graphql -f query="{repository(owner:\"${REPO%%/*}\",name:\"${REPO##*/}\"){issue(number:$n){number closedAt comments(last:100){nodes{createdAt body}} timelineItems(itemTypes:[CROSS_REFERENCED_EVENT,CLOSED_EVENT,CONNECTED_EVENT],first:50){nodes{__typename ... on ClosedEvent{closer{... on PullRequest{mergedAt}}} ... on CrossReferencedEvent{source{... on PullRequest{mergedAt}}} ... on ConnectedEvent{subject{... on PullRequest{mergedAt}}}}}}}}" 2>/dev/null \
  | N=$n jq -r "$FILTER"
done
