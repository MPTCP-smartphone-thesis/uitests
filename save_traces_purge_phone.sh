#! /bin/bash
[ "$1" != "" ] && TRACE_DIR=$1 || TRACE_DIR="~/Thesis/TCPDump"

now=$(date +"%Y_%m_%d_%H_%m_%S")

# compress files
adb shell "tar -cJf /storage/sdcard0/traces_$now.tar.xz /storage/sdcard0/traces*"

# need to add an entry 'mptcpdata' in ~/.ssh/config and load your SSH key in your SSH Agent (via ssh-add)
# or use sshpass: rsync $TRACE_DIR --rsh='sshpass -p PASSWORD ssh -l USER' host.example.com:path
echo "Launch RSync"
rsync -az $TRACE_DIR mptcpdata:/home/mptcp/smartphone || exit 1

echo "Remove files from the phone"
adb shell "rm -r /storage/sdcard0/traces*"
