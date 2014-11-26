#! /bin/bash
# Usage: ./stop_full_pcap_listener.sh

BASE="/home/mptcp/smartphone"
STOP_FILE="$BASE/.tcpdump-stop"
PID_FILE="$BASE/.tcpdump-pid"

> $STOP_FILE
while inotifywait -e modify $STOP_FILE; do
   for pid in $(cat $PID_FILE); do
      kill -15 $pid
   done
   rm -f $PID_FILE
done
