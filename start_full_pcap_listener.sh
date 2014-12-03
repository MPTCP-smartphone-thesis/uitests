#! /bin/bash
# Usage: ./start_full_pcap_listener.sh [interface]

[ "$1" != "" ] && IF=$1 || IF="veth9f9dc66"

BASE="/home/mptcp/smartphone"
FILE="$BASE/.tcpdump-start"
OUT="$BASE-server"
PID="$BASE/.tcpdump-pid"
TIMEOUT=300 # 5 minutes

> $FILE
chmod 777 "$FILE"
while inotifywait -e modify "$FILE"; do
   # The last line of .tcpdump-start contains the name of the application
   CURR_APP=$(tail -n 1 "$FILE" || echo "UNKNOWN")
   timeout $TIMEOUT tcpdump -i $IF -w "${OUT}/${CURR_APP}.pcap" &
   echo $! >> "$PID"
done
