#! /bin/bash
FILE="$1"
shift
ARGS="$@"
$(dirname $0)/start_full_pcap_distant.sh $FILE sshtunnel $ARGS
