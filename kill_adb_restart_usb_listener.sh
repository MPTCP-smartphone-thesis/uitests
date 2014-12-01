#! /bin/bash
# Usage: ./kill_adb_restart_usb_listener.sh [bus]
# To be launched as root

[ "$1" != "" ] && BUS=$1  || BUS="1-6"
[ "$2" != "" ] && FILE=$2 || FILE="/home/mptcp/uitests/.adb_reboot"


> "$FILE"
while inotifywait -e modify "$FILE"; do
    echo "Kill adb server"
    adb kill-server
    sleep 1

    echo "Unbind bus $BUS"
    echo "$BUS" | tee /sys/bus/usb/drivers/usb/unbind
    sleep 1

    echo "Bind bus $BUS"
    echo "$BUS" | tee /sys/bus/usb/drivers/usb/bind
done
