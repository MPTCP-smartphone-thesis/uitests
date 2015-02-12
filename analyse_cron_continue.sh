#!/bin/bash

STOP_FILE="/home/mptcp/smartphone/.analyse-start.pid.stop"
test ! -f "$STOP_FILE"

PID=$(tail -n 1 "$STOP_FILE")
test -z "$PID" && exit 0 # no pid
test ! -d /proc/$PID && exit 0 # no active pid
grep -c "analyze\.py" /proc/$PID/cmdline || exit 0 # not analyze.py

kill -CONT $PID
