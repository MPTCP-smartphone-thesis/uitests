#!/bin/bash
## Docker
# SSH Tunnel: we need to dump traffic
docker start ssh-tunnel
IFCONFIG=$(/sbin/ifconfig | grep veth)
IFSSHTUNNEL="${IFCONFIG:0:11}"

# ShadowSocks: we also need to dump traffic
docker start shadowsocks-c
IFCONFIGHEAD=$(/sbin/ifconfig | grep veth | head -n 1)
IFGREP="${IFCONFIGHEAD:0:11}"
if [ "$IFSSHTUNNEL" != "$IFGREP" ]; then
        IFSHADOWSOCKS="$IFGREP"
else
        IFCONFIGTAIL=$(/sbin/ifconfig | grep veth | tail -n 1)
        IFSHADOWSOCKS="${IFCONFIGTAIL:0:11}"
fi

# Collect full
/home/mptcp/uitests/start_sshtunnel_full_pcap_listener.sh $IFSSHTUNNEL &
/home/mptcp/uitests/start_shadowsocks_full_pcap_listener.sh $IFSHADOWSOCKS &
/home/mptcp/uitests/stop_full_pcap_listener.sh &
/home/mptcp/uitests/rm_full_pcap_listener.sh &
/home/mptcp/uitests/gzip_full_pcap_listener.sh &

# Other:
docker start ripe janus ssh-simple openvpn collectd
