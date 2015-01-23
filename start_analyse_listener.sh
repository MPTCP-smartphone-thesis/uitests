#! /bin/bash
# Usage: ./start_analyse_listener.sh [ANALYSE_DIR]

[ "$1" != "" ] && ANALYSE_DIR=$1 || ANALYSE_DIR="/home/mptcp/smartphone/pcap-measurement"

FILE="/home/mptcp/smartphone/.analyse-start"
PID="$FILE.pid"

cd "$ANALYSE_DIR"

> $FILE
chmod 777 "$FILE"
while inotifywait -e modify "$FILE"; do
    git pull

    # The last line of .analyse-start contains the directory to analyse
    DIR=$(tail -n 1 "$FILE" || echo "UNKNOWN")
    OUT_DIR="pcap/"$(basename $DIR)
    mkdir -p "$OUT_DIR"
    LOG="$OUT_DIR/log_$(date +%Y%m%d_%H%M%S).txt"
    git describe --abbrev=0 --dirty --always > "$LOG"

    # -c clean, -b no graph when using < 1k, -P keep cleaned traces, -j 4 jobs
    ./analyze.py -i "$DIR" -c -b 1000 -P -j 4 >> "$LOG" & # accepts other jobs
    echo $! >> "$PID"
done
