#!/bin/bash
# Computer-use helper for qa-explore: one action with a saved shot, or a timed wait for a text.
# Needs: the `orca` CLI, python3. Set CU_APP to the app (bundle id, name or pid:N) and W to the run folder.
#
#   cu.sh act <name> <orca computer subcommand> [args...]
#       Runs the action, saves the shot as $W/ev/<name>.raw.png, and prints the action's
#       verification and the tree. Q='a|b' prints only the lines with a or b. N=<chars> caps the output.
#   cu.sh wait-for <text> [--count n] [--timeout s] [--every s]
#       Reads the full tree until <text> shows at least n times (default 1). Prints the elapsed
#       seconds and the 4 lines after the last match. Exit 1 on time-out. The shot of the last read
#       is $W/ev/wait-<epoch>.raw.png.
#
# Each read is a full get-app-state WITH a screenshot: a read with --no-screenshot can give an old tree.
set -euo pipefail
: "${CU_APP:?set CU_APP, such as com.github.Electron}"
: "${W:?set W to the run folder}"
mkdir -p "$W/ev"
cmd=${1:-}; shift || true

py_show() { # $1 json file, $2 shot name
  python3 - "$1" "$2" "$W" <<'PY'
import json, os, shutil, sys
path, name, W = sys.argv[1:4]
try:
    d = json.load(open(path))
except Exception:
    print(open(path).read()[:2000]); sys.exit(1)
if d.get("error"):
    print("ERROR", json.dumps(d["error"])[:800]); sys.exit(1)
r = d.get("result", d)
a = r.get("action") or {}
if a:
    print("ACTION", json.dumps({k: a[k] for k in ("verification", "delivery") if k in a}))
p = (r.get("screenshot") or {}).get("path")
if p:
    dst = f"{W}/ev/{name}.raw.png"; shutil.copy(p, dst); print("SHOT", dst)
lines = (r.get("snapshot") or {}).get("treeText", "").splitlines()
q = os.environ.get("Q")
if q:
    keys = [k.lower() for k in q.split("|")]
    lines = [l for l in lines if any(k in l.lower() for k in keys)]
print("\n".join(lines)[: int(os.environ.get("N", "5000"))])
PY
}

case "$cmd" in
  act)
    name=$1; shift
    out="$W/.cu-last.json"
    orca computer "$@" --app "$CU_APP" --json > "$out" 2>&1 || true
    py_show "$out" "$name"
    ;;
  wait-for)
    text=$1; shift; count=1; timeout=180; every=3
    while [ $# -gt 0 ]; do
      case $1 in --count) count=$2;; --timeout) timeout=$2;; --every) every=$2;; *) echo "bad flag $1" >&2; exit 2;; esac
      shift 2
    done
    t0=$(python3 -c 'import time;print(time.time())')
    while :; do
      out="$W/.cu-wait.json"
      orca computer get-app-state --app "$CU_APP" --json > "$out" 2>&1 || true
      res=$(python3 - "$out" "$text" "$count" "$t0" <<'PY'
import json, sys, time
path, text, count, t0 = sys.argv[1], sys.argv[2], int(sys.argv[3]), float(sys.argv[4])
try:
    lines = json.load(open(path))["result"]["snapshot"]["treeText"].splitlines()
except Exception:
    lines = []
hits = [i for i, l in enumerate(lines) if text in l]
el = round(time.time() - t0, 1)
if len(hits) >= count:
    after = [l.strip()[:200] for l in lines[hits[-1] + 1 : hits[-1] + 5]]
    print(f"FOUND {el}s copies={len(hits)}\n" + "\n".join(after))
else:
    print(f"WAIT {el}s copies={len(hits)}")
PY
)
      echo "$res" | head -1
      if [[ $res == FOUND* ]]; then
        echo "$res" | tail -n +2
        py_show "$out" "wait-$(date +%s)" | grep '^SHOT' || true
        exit 0
      fi
      el=${res#WAIT }; el=${el%%s*}
      if python3 -c "import sys;sys.exit(0 if float('$el')>=$timeout else 1)"; then echo "TIMEOUT after ${el}s"; exit 1; fi
      sleep "$every"
    done
    ;;
  *) sed -n 2,13p "$0"; exit 2;;
esac
