#! /bin/bash
# Usage: .stop_pcap_when_test_completed.sh

> /home/mptcp/smartphone/.tcpdump-stop
while inotifywait -e modify /home/mptcp/smartphone/.tcpdump-stop; do
   for pid in $ (cat /home/mptcp/smartphone/.tcpdump-pid); do
      kill pid
   done
   rm /home/mptcp/smartphone/.tcpdump-pid
done
