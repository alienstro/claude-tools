#!/bin/zsh
# Drive any visible desktop app window through `orca computer` (computer use), for QA proof.
# Works for chat apps (Telegram, WhatsApp, Slack, Discord), native apps, simulators and browser windows.
#
# Usage: app.sh <app> <command> [args]
#   <app>  a bundle id or app name from `orca computer list-apps` (for example com.tdesktop.Telegram)
#
#   tree [n]                         print the last n lines of the accessibility tree
#   find "<regex>"                   print tree lines that match (to get an element index)
#   send "<field-regex>" "<text>"    set the text of the first editable field whose tree line matches, then press Return
#   type "<text>"                    type into the focused field (after a click), then press Return
#   click <index>                    click an element by its tree index (take a fresh `tree` first)
#   key <key> | hotkey <chord>       press a key (Return, Escape, Up) or a chord (CmdOrCtrl+A)
#   shot <out.png> [crop]            save a screenshot; crop = "x0,y0,x1,y1" in fractions of the window (default 0,0,1,1)
#   tap <x> <y>                      click a point given in pixels of the LAST shot (crop and scale are undone for you)
#   wait "<regex>" [sec] [skip-regex]
#                                    poll the tree until a line matches regex (default 150 s); lines that match
#                                    skip-regex are ignored (for example your own sent messages)
#
# ORCA_BIN selects the Orca executable (default: orca).
O=${ORCA_BIN:-orca}
APP=$1; CMD=$2; shift 2
[ -z "$CMD" ] && { sed -n '2,22p' "$0"; exit 1; }
KEY=$(printf '%s' "$APP" | tr -c 'A-Za-z0-9' '_')
ST=${TMPDIR:-/tmp}/qa-e2e-app-$KEY-state.json
LAST=${TMPDIR:-/tmp}/qa-e2e-app-$KEY-lastshot.txt
state() { $O computer get-app-state --app "$APP" --restore-window ${1:-} --json > $ST 2>&1; }
tree() { jq -r '.result.snapshot.treeText // empty' $ST; }
ok() { jq -c '{ok, error: .error.code, verification: .result.verification}'; }

case $CMD in
  tree) state --no-screenshot; tree | tail -${1:-60} ;;
  find) state --no-screenshot; tree | grep -E "$1" ;;
  send)
    state --no-screenshot
    idx=$(tree | grep -E 'settable' | grep -m1 -E "$1" | awk '{print $1}')
    [ -z "$idx" ] && { echo "no editable field matches \"$1\". If the tree is empty (only a dialog), click the field by coordinates and use: type"; tree | head -8; exit 1; }
    printf '%s' "$2" | $O computer set-value --app "$APP" --element-index $idx --value-stdin --no-screenshot --json | ok
    $O computer press-key --app "$APP" --key Return --no-screenshot --json | ok ;;
  type)
    $O computer type-text --app "$APP" --text "$1" --no-screenshot --json | ok
    $O computer press-key --app "$APP" --key Return --no-screenshot --json | ok ;;
  click) $O computer click --app "$APP" --element-index "$1" --restore-window --no-screenshot --json | ok ;;
  key) $O computer press-key --app "$APP" --key "$1" --no-screenshot --json | ok ;;
  hotkey) $O computer hotkey --app "$APP" --key "$1" --no-screenshot --json | ok ;;
  shot)
    OUT=$1; CROP=${2:-0,0,1,1}; state
    p=$(jq -r '.result.screenshot.path // empty' $ST); sc=$(jq -r '.result.screenshot.scale // 1' $ST)
    [ -z "$p" ] && { echo "no screenshot: $(jq -c .error $ST)"; exit 1; }
    python3 - "$p" "$OUT" "$CROP" "$sc" > $LAST <<'PY'
import sys
from PIL import Image
src, out, crop, sc = sys.argv[1], sys.argv[2], [float(v) for v in sys.argv[3].split(",")], sys.argv[4]
im = Image.open(src); w, h = im.size
box = (int(w*crop[0]), int(h*crop[1]), int(w*crop[2]), int(h*crop[3]))
im.crop(box).save(out)
print(box[0], box[1], sc)
PY
    echo "$OUT" ;;
  tap)
    [ -s $LAST ] || { echo "take a shot first"; exit 1; }
    read x0 y0 sc < $LAST
    px=$(python3 -c "print(round(($1+$x0)/$sc))"); py=$(python3 -c "print(round(($2+$y0)/$sc))")
    $O computer click --app "$APP" --x $px --y $py --restore-window --no-screenshot --json | ok ;;
  wait)
    RE=$1; LIM=${2:-150}; SKIP=${3:-'^$'}; end=$((SECONDS+LIM))
    while [ $SECONDS -lt $end ]; do
      state --no-screenshot
      tree | grep -vE "$SKIP" | grep -qE "$RE" && { echo "matched"; tree | grep -vE "$SKIP" | grep -E "$RE" | tail -3 | cut -c1-300; exit 0; }
      sleep 6
    done
    echo "timeout after ${LIM}s"; exit 2 ;;
  *) sed -n '2,22p' "$0"; exit 1 ;;
esac
