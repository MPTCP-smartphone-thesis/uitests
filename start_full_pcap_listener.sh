#! /bin/bash
# Usage: ./start_full_pcap_listener.sh interface endfile
#  e.g.: ./start_full_pcap_listener.sh veth0cf65f5 sshtunnel

[ "$1" = "" ] && echo "No IFace: exit" && exit 1

IF="$1"
MODE="$2"
BASE="/home/mptcp/smartphone"
FILE="$BASE/.tcpdump-start-$MODE"
OUT="$BASE-server"
PID="$BASE/.tcpdump-pid" # same for all modes: should not run both at the same time!
TIMEOUT=300 # 5 minutes

> $FILE
chmod 777 "$FILE"
while inotifywait -e modify "$FILE"; do
   # The last line of .tcpdump-start-* contains the name of the application
   CURR_APP=$(tail -n 1 "$FILE" || echo "UNKNOWN")
   timeout $TIMEOUT /usr/sbin/tcpdump -i $IF -w "${OUT}/${MODE}_${CURR_APP}.pcap" &
   echo $! >> "$PID"
done
