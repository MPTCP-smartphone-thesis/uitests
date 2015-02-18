#! /bin/bash
# Usage: ./start_analyse_listener.sh [ANALYSE_DIR]

[ "$1" != "" ] && ANALYSE_DIR=$1 || ANALYSE_DIR="/home/mptcp/smartphone/pcap-measurement"

FILE="/home/mptcp/smartphone/.analyse-start"
PID="$FILE.pid"
CORES=2 # just used two threads: we need to lock for matplotlib, no need to consumes lot of ram just to wait
#CORES=$(grep -c "^processor" /proc/cpuinfo)
#CORES=$(($CORES + $CORES/2)) # we have locks which take time

cd "$ANALYSE_DIR"

> $FILE
chmod 777 "$FILE"
while inotifywait -e modify "$FILE"; do
    git pull

    # The last line of .analyse-start contains the directory to analyse
    LAST_LINE=$(tail -n 1 "$FILE" || echo "UNKNOWN")

    DIR=$(echo $LAST_LINE | awk '{print $1}')
    SERVER_DIR=$(echo $DIR | sed -e 's#/smartphone/#/smartphone-server/#g')

    ARGS=$(echo $LAST_LINE | awk '{$1=""; print $0}')
    # -j 4 jobs
    test -z "$ARGS" && ARGS="-j $CORES"

    OUT_DIR="pcap/"$(basename $DIR)
    mkdir -p "$OUT_DIR"
    LOG_NAME="$OUT_DIR/log_$(date +%Y%m%d_%H%M%S)"
    LOG="${LOG_NAME}_any.txt"
    LOG_SERVER="${LOG_NAME}_server.txt"

    GIT=$(git describe --abbrev=0 --dirty --always)
    echo $GIT > "$LOG"
    echo $GIT > "$LOG_SERVER"

    # For any
    ./analyze.py -i "$DIR" $ARGS >> "$LOG" 2>&1 & # accepts other jobs
    # For the server (/smartphone-server/, with 'server' prefix)
    ./analyze.py -i "$SERVER_DIR" -p '_server.' $ARGS >> "$LOG_SERVER" 2>&1 & # accepts other jobs
    echo $! >> "$PID"
done
