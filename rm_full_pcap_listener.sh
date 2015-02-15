#! /bin/bash
# Usage: ./rm_full_pcap_listener.sh

BASE="/home/mptcp/smartphone"
FILE="$BASE/.tcpdump-rm"
OUT="$BASE-server"

> $FILE
chmod 777 "$FILE"
while inotifywait -e modify "$FILE"; do
    # The last line of .tcpdump-rm contains the file (basename) to delete
    CURR_APP=$(tail -n 1 "$FILE" || continue)
    sleep 1 # tcpdump need time to write file
    rm "${OUT}/${CURR_APP}.pcap"
done
