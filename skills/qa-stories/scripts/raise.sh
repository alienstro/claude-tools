#!/bin/zsh
# Brings the first window of a process to the front, so that foreground clicks
# and shots reach it. A covered Electron window does not repaint.
# Usage: raise.sh <pid>
[ -z "$1" ] && { echo "Usage: raise.sh <pid>"; exit 1; }
osascript -e "tell application \"System Events\" to tell (first process whose unix id is $1)" \
  -e 'set frontmost to true' -e 'perform action "AXRaise" of window 1' -e 'end tell' >/dev/null
