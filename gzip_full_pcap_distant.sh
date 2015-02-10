#! /bin/bash
[ "$1" != "" ] && SSH_USER=$1  || SSH_USER="mptcpdata"
[ "$2" != "" ] && DEST_FILE=$2 || DEST_FILE="/home/mptcp/smartphone/.tcpdump-gzip"

MESSAGES=$(date -R)
echo "ssh $SSH_USER \"echo $MESSAGES >> $DEST_FILE\""
ssh $SSH_USER "echo $MESSAGES >> $DEST_FILE"
