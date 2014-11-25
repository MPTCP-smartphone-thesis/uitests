#! /bin/bash
# Usage: ./stop_full_pcap_listener.sh

> /home/mptcp/smartphone/.tcpdump-stop
while inotifywait -e modify /home/mptcp/smartphone/.tcpdump-stop; do
   for pid in $(cat /home/mptcp/smartphone/.tcpdump-pid); do
      kill $pid
   done
   rm /home/mptcp/smartphone/.tcpdump-pid
done
