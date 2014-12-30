#!/bin/bash
[ -n "$1" ] && IFACE="$1" || read -p "IFace to capture? (e.g. lo, wlan0, rmnet0) " IFACE
if [ -n "$2" ]; then
	FILTER="tcp and not port $2"
elif [ "$IFACE" = "lo" ]; then
	read -p "Port used by Redsocks? (e.g. 1984, 1080) " PORT
	FILTER="tcp and not port $PORT"
else
	FILTER="tcp"
fi
echo "Capturing on $IFACE with this filter: $FILTER"

adb forward tcp:31337 tcp:31337

sudo -v
adb shell "su - sh -c 'tcpdump -i $IFACE -s 1514 -w - -nS $FILTER and not port 31337 | netcat -l -p 31337'" &

echo "Wait 5 seconds before launching wireshark"
sleep 5
netcat localhost 31337 | sudo wireshark -i - -kS &
NETCAT_PID=$!

echo -e "\n\tPress Enter when it's finished\n"
read
ps aux | grep "[ ]$NETCAT_PID " && kill $NETCAT_PID
adb shell 'su - sh -c "kill $(pidof tcpdump)"'
