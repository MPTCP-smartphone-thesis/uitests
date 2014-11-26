#! /bin/bash
# Usage: ./start_full_pcap_listener.sh [interface]

[ "$1" != "" ] && IF=$1 || IF="veth3426f38"

BASE="/home/mptcp/smartphone"
FILE="$BASE/.tcpdump-start"
OUT="$BASE-server"
PID="$BASE/.tcpdump-pid"

> $FILE
while inotifywait -e modify "$FILE"; do
   # The last line of .tcpdump-start contains the name of the application
   CURR_APP=$(tail -n 1 "$FILE" || echo "UNKNOWN")
   tcpdump -i $IF -w "${OUT}/${CURR_APP}.pcap" &
   echo $! >> "$PID"
done
