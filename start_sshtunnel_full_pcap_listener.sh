#! /bin/bash
IFACE="$1"
$(dirname $0)/start_full_pcap_listener.sh "$IFACE" sshtunnel
