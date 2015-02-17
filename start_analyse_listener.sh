#! /bin/bash
# Usage: ./start_analyse_listener.sh [ANALYSE_DIR]

[ "$1" != "" ] && ANALYSE_DIR=$1 || ANALYSE_DIR="/home/mptcp/smartphone/pcap-measurement"

FILE="/home/mptcp/smartphone/.analyse-start"
PID="$FILE.pid"
CORES=$(grep -c "^processor" /proc/cpuinfo)
CORES=$(($CORES + $CORES/2)) # we have locks which take time

cd "$ANALYSE_DIR"

> $FILE
chmod 777 "$FILE"
while inotifywait -e modify "$FILE"; do
    git pull

    # The last line of .analyse-start contains the directory to analyse
    LAST_LINE=$(tail -n 1 "$FILE" || echo "UNKNOWN")
    DIR=$(echo $LAST_LINE | awk '{print $1}')
    ARGS=$(echo $LAST_LINE | awk '{$1=""; print $0}')
    # -j 4 jobs
    test -z "$ARGS" && ARGS="-j $CORES"
    OUT_DIR="pcap/"$(basename $DIR)
    mkdir -p "$OUT_DIR"
    LOG="$OUT_DIR/log_$(date +%Y%m%d_%H%M%S).txt"
    git describe --abbrev=0 --dirty --always > "$LOG"

    ./analyze.py -i "$DIR" $ARGS >> "$LOG" 2>>&1 & # accepts other jobs
    echo $! >> "$PID"
done
