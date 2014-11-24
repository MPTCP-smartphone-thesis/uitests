#! /bin/bash
# Usage: ./create_pcap_when_test_started.sh the_file

[ "$1" != "" ] && THE_FILE=$1

> /home/mptcp/smartphone/.tcpdump-start 
while inotifywait -e modify /home/mptcp/smartphone/.tcpdump-start; do
   CURR_APP=$(cat /home/mptcp/smartphone/.tcpdump-start | tail -n 1)
   tcpdump -i veth3426f38 -w "/home/mptcp/smartphone-server/${CURR_APP}.pcap" || echo $! > /home/mptcp/smartphone/.tcpdump-pid
done
