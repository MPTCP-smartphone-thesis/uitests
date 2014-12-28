#! /bin/bash
[ "$1" = "" ] && echo "No message: exit" && exit 1
[ "$2" = "" ] && echo "No destination: exit" && exit 1

MESSAGES=$1
DEST_FILE="/home/mptcp/smartphone/.tcpdump-start-$2"
SSH_USER="mptcpdata"

echo "ssh $SSH_USER \"echo $MESSAGES >> $DEST_FILE\""
ssh $SSH_USER "echo $MESSAGES >> $DEST_FILE"
