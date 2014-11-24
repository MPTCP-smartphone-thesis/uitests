#! /bin/bash
# Usage: ./create_pcap_when_test_started.sh [interface]

[ "$1" != "" ] && IF=$1 || IF="veth3426f38"

> /home/mptcp/smartphone/.tcpdump-start 
while inotifywait -e modify /home/mptcp/smartphone/.tcpdump-start; do
   # The last line of .tcpdump-start contains the name of the application
   CURR_APP=$(cat /home/mptcp/smartphone/.tcpdump-start | tail -n 1)
   tcpdump -i $IF -w "/home/mptcp/smartphone-server/${CURR_APP}.pcap" & | echo $! >> /home/mptcp/smartphone/.tcpdump-pid
done
