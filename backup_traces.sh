#! /bin/bash
[ "$1" != "" ] && TRACE_DIR=$1 || TRACE_DIR="/home/mptcp/Thesis/TCPDump"
[ "$2" != "" ] && DEST_DIR=$2 || DEST_DIR="/home/mptcp/smartphone"
[ "$3" != "" ] && SSH_USER=$3 || SSH_USER="mptcpdata"

RC=0

# need to add an entry 'mptcpdata' in ~/.ssh/config and load your SSH key in your SSH Agent (via ssh-add)
# or use sshpass: rsync $TRACE_DIR --rsh='sshpass -p PASSWORD ssh -l USER' host.example.com:path
echo "Launch RSync"
rsync -az --progress $TRACE_DIR $SSH_USER:$DEST_DIR
