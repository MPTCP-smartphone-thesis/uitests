#! /bin/bash
[ "$1" != "" ] && MESSAGES=$1  || exit 1
[ "$2" != "" ] && SSH_USER=$2  || SSH_USER="mptcpdata"
[ "$3" != "" ] && DEST_FILE=$3 || DEST_FILE="/home/mptcp/smartphone/.tcpdump-rm"

echo "ssh $SSH_USER \"echo $MESSAGES >> $DEST_FILE\""
ssh $SSH_USER "echo $MESSAGES >> $DEST_FILE"
