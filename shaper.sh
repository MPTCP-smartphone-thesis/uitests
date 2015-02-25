#!/bin/sh
#
# With the help of Nicolargo's limitbw script and OpenWRT's WShaper tool:
# limitbw: http://blog.nicolargo.com/2009/03/simuler-un-lien-wan-sous-linux.html

test -n "$1" && ACTION=$1 && shift || ACTION='help'
# Interface name (e.g. eth0.2)
test -n "$1" && IFUP=$1 && shift || ACTION='errorif'
test -n "$1" && IFDOWN=$1 && shift || ACTION='errorif'

MODULES='sch_ingress sch_sfq sch_htb cls_u32 act_police'

# To be launched after having used 'start' method
addnetem() {
    echo "Add Netem: $@"
    rc=0
    # upload
    tc qdisc del dev $IFUP parent 1:10 handle 10: || rc=$?
    tc qdisc add dev $IFUP parent 1:10 handle 10: netem $@ || rc=$?
    tc qdisc del dev $IFUP parent 1:20 handle 20: || rc=$?
    tc qdisc add dev $IFUP parent 1:20 handle 20: netem $@ || rc=$?
    tc qdisc del dev $IFUP parent 1:30 handle 30: || rc=$?
    tc qdisc add dev $IFUP parent 1:30 handle 30: netem $@ || rc=$?
    # download
    tc qdisc del dev $IFDOWN parent 1:10 handle 10: || rc=$?
    tc qdisc add dev $IFDOWN parent 1:10 handle 10: netem $@ || rc=$?
    return $rc
}

# To be launched after having used 'start' method
chnetem() {
    echo "Change Netem: $@"
    rc=0
    # upload
    tc qdisc change dev $IFUP parent 1:10 handle 10: netem $@ || rc=$?
    tc qdisc change dev $IFUP parent 1:20 handle 20: netem $@ || rc=$?
    tc qdisc change dev $IFUP parent 1:30 handle 30: netem $@ || rc=$?
    # download
    tc qdisc change dev $IFDOWN parent 1:10 handle 10: netem $@ || rc=$?
    return $rc
}

# To be launched after having used 'start' method: mgbw add 1000 15000 => up: 1M
chbw() {
    UPLINK=$1
    DOWNLINK=$2
    echo "BW: $@"
    rc=0
    # Upload
    tc class change dev $IFUP parent 1:  classid 1:1  htb rate ${UPLINK}kbit burst 6k || rc=$?
    tc class change dev $IFUP parent 1:1 classid 1:10 htb rate ${UPLINK}kbit burst 6k prio 1 || rc=$?
    tc class change dev $IFUP parent 1:1 classid 1:20 htb rate $((9*$UPLINK/10))kbit burst 6k prio 2 || rc=$?
    tc class change dev $IFUP parent 1:1 classid 1:30 htb rate $((8*$UPLINK/10))kbit burst 6k prio 2 || rc=$?
    # Download
    tc class change dev $IFDOWN parent 1:  classid 1:1  htb rate ${DOWNLINK}kbit burst 10k || rc=$?
    tc class change dev $IFDOWN parent 1:1 classid 1:10 htb rate ${DOWNLINK}kbit burst 10k prio 1 || rc=$?
    return $rc
}

start() {
    UPLINK=$1
    shift
    DOWNLINK=$1
    shift
    NETEM="$@"

    for i in $MODULES; do
        modprobe $i > /dev/null
    done

    # From OpenWRT's WShaper script:
    ###### uplink

    # install root HTB, point default traffic to 1:20:
    tc qdisc add dev $IFUP handle 1: root htb default 20

    # shape everything at $UPLINK speed - this prevents huge queues in your
    # DSL modem which destroy latency:
    tc class add dev $IFUP parent 1: classid 1:1 htb rate ${UPLINK}kbit burst 6k

    # high prio class 1:10:
    tc class add dev $IFUP parent 1:1 classid 1:10 htb rate ${UPLINK}kbit burst 6k prio 1

    # bulk & default class 1:20 - gets slightly less traffic, and a lower priority:
    tc class add dev $IFUP parent 1:1 classid 1:20 htb rate $((9*$UPLINK/10))kbit burst 6k prio 2
    tc class add dev $IFUP parent 1:1 classid 1:30 htb rate $((8*$UPLINK/10))kbit burst 6k prio 2

    if test -n "$NETEM"; then
        # Delay/losses
        tc qdisc add dev $IFUP parent 1:10 handle 10: netem $NETEM
        tc qdisc add dev $IFUP parent 1:20 handle 20: netem $NETEM
        tc qdisc add dev $IFUP parent 1:30 handle 30: netem $NETEM
    else
        # all get Stochastic Fairness:
        tc qdisc add dev $IFUP parent 1:10 handle 10: sfq perturb 10
        tc qdisc add dev $IFUP parent 1:20 handle 20: sfq perturb 10
        tc qdisc add dev $IFUP parent 1:30 handle 30: sfq perturb 10
    fi

    # TOS Minimum Delay (ssh, NOT scp) in 1:10:
    tc filter add dev $IFUP parent 1:0 protocol ip prio 10 u32 \
          match ip tos 0x10 0xff  flowid 1:10

    # ICMP (ip protocol 1) in the interactive class 1:10 so we
    # can do measurements & impress our friends:
    tc filter add dev $IFUP parent 1:0 protocol ip prio 10 u32 \
            match ip protocol 1 0xff flowid 1:10

    # To speed up downloads while an upload is going on, put ACK packets in
    # the interactive class:
    tc filter add dev $IFUP parent 1: protocol ip prio 10 u32 \
       match ip protocol 6 0xff \
       match u8 0x05 0x0f at 0 \
       match u16 0x0000 0xffc0 at 2 \
       match u8 0x10 0xff at 33 \
       flowid 1:10
       # match:
       #  * u8: check by 8 bits
       #  * 0x10: value to be matched
       #  * 0xff: mask on which the previous value has to be matched => here, exactly match 0x10 ; if mask = 0x0f, only match last 4 bits.
       #  * at 33: at 33th byte since IP header start.
       # Here: protocol TCP, header length == 5 (20 bytes), max total length header 64 bytes and pure ACK.
       # source: http://lartc.org/howto/lartc.adv-filter.html

    # rest is 'non-interactive' ie 'bulk' and ends up in 1:20
    tc filter add dev $IFUP parent 1: protocol ip prio 18 u32 \
       match ip dst 0.0.0.0/0 flowid 1:20


    ########## downlink #############
    tc qdisc add dev $IFDOWN handle 1: root htb default 10
    tc class add dev $IFDOWN parent 1: classid 1:1 htb rate ${DOWNLINK}kbit burst 10k
    # high prio class 1:10:
    tc class add dev $IFDOWN parent 1:1 classid 1:10 htb rate ${DOWNLINK}kbit burst 10k prio 1
    if test -n "$NETEM"; then
        tc qdisc add dev $IFDOWN parent 1:10 handle 10: netem $@NETEM
    else
        tc qdisc add dev $IFDOWN parent 1:10 handle 10: sfq perturb 10
    fi
}

stop() {
    tc qdisc del dev $IFUP   root 2> /dev/null > /dev/null
    tc qdisc del dev $IFDOWN root 2> /dev/null > /dev/null
    # not needed?
    # for i in $MODULES; do
    #     rmmod $i
    # done
    return 0 # ignore and hide errors
}

restart() {
    rc=0
    stop || rc=$?
    sleep 1
    start $@ || rc=$?
    return $rc
}

show() {
    echo "Interface uplink: $IFUP"
    tc -s qdisc ls dev $IFUP
    tc -s class ls dev $IFUP
    echo "Interface downlink: $IFDOWN"
    tc -s qdisc ls dev $IFDOWN
    tc -s class ls dev $IFDOWN
}

usage() {
    echo "Usage: $0 {start|stop|restart|show|addnetem|chnetem|chbw} IFaceUp IFaceDown [BWup BWdw [netem rules]] [netem rules]"
    echo
    echo "Examples:"
    echo "    ./$0 start   eth0.2 wlan0 2000 15000 delay 50ms 5ms loss 0.5% 25%"
    echo "                                     kbps kbps"
    echo "    ./$0 chnetem eth0.2 wlan0 delay 15ms 2ms loss 0.05% 5%"
    echo "    ./$0 stop    eth0.2 wlan0"
}

case "$ACTION" in
    start)
        echo -n "Starting shaping rules: "
        test -z "$1" -o -z "$2" && echo "No up and down args, exit" && exit 1
        start $@ || exit $?
        echo "done"
    ;;
    stop)
        echo -n "Stopping shaping rules: "
        stop || exit $?
        echo "done"
    ;;
    restart)
        echo -n "Restarting shaping rules: "
        test -z "$1" -o -z "$2" && echo "No up and down args, exit" && exit 1
        restart $@ || exit $?
        echo "done"
    ;;
    show)
        echo "Shaping status for $IF:"
        show
        echo ""
    ;;
    addnetem)
        echo -n "Add Netem rules: "
        test -z "$1" && echo "No netem args, exit" && exit 1
        addnetem $@ || exit $?
        echo "done"
    ;;
    chnetem)
        echo -n "Change Netem rules: "
        test -z "$1" && echo "No netem args, exit" && exit 1
        chnetem $@ || exit $?
        echo "done"
    ;;
    chbw)
        echo -n "Change bandwidth: "
        test -z "$1" -o -z "$2" && echo "No up and down args, exit" && exit 1
        chbw $1 $2 || exit $?
        echo "done"
    ;;
    errorif)
        echo "!! ERROR, no interfaces !!"
        usage
    ;;
    *)
        usage
    ;;
esac

exit 0
