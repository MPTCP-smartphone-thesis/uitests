#! /bin/bash
# Usage: ./start_full_pcap_listener.sh interface endfile
#  e.g.: ./start_full_pcap_listener.sh veth0cf65f5 sshtunnel

[ "$1" = "" ] && echo "No IFace MPTCP: exit" && exit 1
[ "$2" = "" ] && echo "No IFace TCP: exit" && exit 1

IF_MPTCP="$1"
IF_TCP="$2"
BASE="/home/mptcp/smartphone-ice"
FILE="$BASE/.tcpdump-start"
OUT_MPTCP="$BASE/mptcp"
OUT_TCP="$BASE/tcp"
PID="$BASE/.tcpdump-pid" # same for all modes: should not run both at the same time!
TIMEOUT=3600 # 60 minutes
ARGS="-s 100 tcp port 8000"

> $FILE
chmod 777 "$FILE"
while inotifywait -e modify "$FILE"; do
    DATE=$(date +%Y%m%d_%H%M%S)
    timeout $TIMEOUT /usr/sbin/tcpdump -i $IF_MPTCP -w "${OUT_MPTCP}/mptcp_ice_${DATE}.pcap" $ARGS &
    echo "$!" >> "$PID"
    timeout $TIMEOUT /usr/sbin/tcpdump -i $IF_TCP -w "${OUT_TCP}/tcp_ice_${DATE}.pcap" $ARGS &
    echo "$!" >> "$PID"
done
