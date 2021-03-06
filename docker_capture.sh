#!/bin/bash

# increase limit for number of fd: needed at least for ShadowSocks
ulimit -n 4096 # default max value
ulimit -n 51200 # try a bigger one

## Docker
# SSH Tunnel: we need to dump traffic
docker start ssh-tunnel
sleep 0.5
IFSSHTUNNEL=$(grep "docker0: port" /var/log/syslog | tail -n 1 | cut -d\( -f2 | cut -d\) -f1)

# ShadowSocks: we also need to dump traffic
docker start shadowsocks-c
sleep 0.5
IFSHADOWSOCKS=$(grep "docker0: port" /var/log/syslog | tail -n 1 | cut -d\( -f2 | cut -d\) -f1)

docker start shadowsocks-c-assistants
sleep 0.5
IFASSISTANTS=$(grep "docker0: port" /var/log/syslog | tail -n 1 | cut -d\( -f2 | cut -d\) -f1)

# Collect full
/home/mptcp/uitests/start_sshtunnel_full_pcap_listener.sh $IFSSHTUNNEL &
/home/mptcp/uitests/start_shadowsocks_full_pcap_listener.sh $IFSHADOWSOCKS &
/home/mptcp/uitests/stop_full_pcap_listener.sh &
/home/mptcp/uitests/rm_full_pcap_listener.sh &
/home/mptcp/uitests/gzip_full_pcap_listener.sh &

# TCPDump: rotate (500M), only header (120 bytes), compress with gzip
/usr/sbin/tcpdump -i $IFASSISTANTS -w /home/mptcp/smartphone-assistants/dump_$(date +%Y%m%d_%H%M%S) -C 500 -s 120 -z gzip tcp &

# Other:
docker start ripe janus ssh-simple openvpn collectd ssh-simple-benjamin pureftpdfirefox
