#! /bin/bash
# Usage: ./gzip_full_pcap_listener.sh

BASE="/home/mptcp/smartphone"
FILE="$BASE/.tcpdump-gzip"
OUT="$BASE-server"
CORES=$(grep -c '^processor' /proc/cpuinfo)
cd "$OUT"

> $FILE
chmod 777 "$FILE"
while inotifywait -e modify "$FILE"; do
    find . -name "*.pcap" -type f -print0 | xargs -0 -n 1 -P $CORES gzip -9
done
