#!/bin/bash

PID_FILE="/home/mptcp/smartphone/.analyse-start.pid"
STOP_FILE="$PID_FILE.stop"
rm -f "$STOP_FILE"

PID=$(tail -n 1 "$PID_FILE")
test -z "$PID" && exit 0 # no pid
test ! -d /proc/$PID && exit 0 # no active pid
grep -c "analyze\.py" /proc/$PID/cmdline || exit 0 # not analyze.py

kill -STOP $PID
echo $PID > "$STOP_FILE"
