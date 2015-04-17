#! /bin/bash
DEST_FILE="/home/mptcp/smartphone-ice/.tcpdump-start"
SSH_USER="mptcpdata"
DATE=$(date +%Y%m%d_%H%M%S)

echo "ssh $SSH_USER \"echo $DATE >> $DEST_FILE\""
ssh $SSH_USER "echo $DATE >> $DEST_FILE"
