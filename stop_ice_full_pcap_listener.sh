#! /bin/bash
# Usage: ./stop_full_pcap_listener.sh

BASE="/home/mptcp/smartphone-ice"
STOP_FILE="$BASE/.tcpdump-stop"
PID_FILE="$BASE/.tcpdump-pid"

> $STOP_FILE
chmod 777 "$STOP_FILE"
while inotifywait -e modify $STOP_FILE; do
    # Stop tcpdump
    for PID in $(cat $PID_FILE); do
        test -z "$PID" && continue # no PID
        test ! -d /proc/$PID && continue # no active PID
        grep -c "tcpdump" /proc/$PID/cmdline || continue # not tcpdump
        kill -15 $PID
    done
    rm -f $PID_FILE
done
