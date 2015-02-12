#!/bin/bash
test -z "$1" && echo "No dir, exit" && exit 1
test ! -d "$1" && echo "Dir '$1' doesn't exist, exit" && exit 1

FULLDIR=$1
DIR=$(basename $FULLDIR)
test -z "$DIR" && echo "No dir? exit!"
CORES=$(grep -c "^processor" /proc/cpuinfo)
CORES=$(($CORES + $CORES/2)) # we have locks which take time

test ! -d "traces/$DIR" && echo "Dir 'traces/$DIR' doesn't exist in the current dir, exit" && exit 1

rm -rf aggls/$DIR graphs/$DIR stats/$DIR
echo "$FULLDIR -b 1000 -P -j $CORES -l -C" >> /home/mptcp/smartphone/.analyse-start
