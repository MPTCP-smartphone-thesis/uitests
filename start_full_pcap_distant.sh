#! /bin/bash
[ "$1" = "" ] && echo "No message: exit" && exit 1
FILE=$1
shift
[ "$1" = "" ] && echo "No destination: exit" && exit 1
DEST_FILE="/home/mptcp/smartphone/.tcpdump-start-$1"
shift
ARGS="$@"

SSH_USER="mptcpdata"

echo "ssh $SSH_USER \"echo $FILE $ARGS >> $DEST_FILE\""
ssh $SSH_USER "echo $FILE $ARGS >> $DEST_FILE"
