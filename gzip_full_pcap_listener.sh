#! /bin/bash
# Usage: ./gzip_full_pcap_listener.sh

BASE="/home/mptcp/smartphone"
FILE="$BASE/.tcpdump-gzip"
OUT="$BASE-server"

cd "$OUT"

> $FILE
chmod 777 "$FILE"
while inotifywait -e modify "$FILE"; do
   for i in "*.pcap"; do
       gzip -9 $i
   done
done
