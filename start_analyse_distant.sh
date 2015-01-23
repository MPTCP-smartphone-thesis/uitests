#! /bin/bash
[ "$1" = "" ] && echo "No directory: exit" && exit 1

DIR="/home/mptcp/smartphone/$1"
DEST_FILE="/home/mptcp/smartphone/.analyse-start"
SSH_USER="mptcpdata"

echo "ssh $SSH_USER \"echo $DIR >> $DEST_FILE\""
ssh $SSH_USER "echo $DIR >> $DEST_FILE"
