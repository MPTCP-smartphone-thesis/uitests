#!/bin/sh
#
# With the help of Nicolargo's limitbw script and OpenWRT's WShaper tool:
# limitbw: http://blog.nicolargo.com/2009/03/simuler-un-lien-wan-sous-linux.html

test -n "$1" && ACTION=$1 && shift || ACTION='help'
# Interface name (e.g. eth0.2)
test -n "$1" && IFUP=$1 && shift || ACTION='errorif'
test -n "$1" && IFDOWN=$1 && shift || ACTION='errorif'

MODULES='sch_netem sch_htb cls_u32 act_police'
FILTER=0

# if no delay, add 0ms delay to add a queue.
get_netem_delay() {
    NETEM="$@"
    test "${NETEM#*delay}" = "$NETEM" && NETEM="$NETEM delay 0ms" # limit 4375" # (10M/8*7m/2)
    echo "$NETEM"
}

mg_netem_up() {
    STATUS=$1
    shift
    LIMIT=$1
    shift
    NETEM="$(get_netem_delay $@)"
    rc=0

    tc qdisc $STATUS dev $IFUP parent 1:10 handle 10: netem $NETEM limit $LIMIT || rc=$?
    if test $FILTER -eq 1; then
        tc qdisc $STATUS dev $IFUP parent 1:20 handle 20: netem $NETEM limit $((9*$LIMIT/10)) || rc=$?
        tc qdisc $STATUS dev $IFUP parent 1:30 handle 30: netem $NETEM limit $((8*$LIMIT/10)) || rc=$?
    fi

    return $rc
}

mg_netem_down() {
    STATUS=$1
    shift
    LIMIT=$1
    shift
    NETEM="$(get_netem_delay $@) limit $LIMIT"
    rc=0

    tc qdisc $STATUS dev $IFDOWN parent 1:10 handle 10: netem $NETEM || rc=$?

    return $rc
}

# To be launched after having used 'start' method
netem() {
    LIMIT_UP=$1
    shift
    LIMIT_DW=$1
    shift
    NETEM="$@"
    echo -n "Change Netem: $NETEM "
    rc=0
    mg_netem_up change $LIMIT_UP $NETEM || rc=$?
    mg_netem_down change $LIMIT_DW $NETEM || rc=$?
    return $rc
}

mg_bw_up() {
    STATUS=$1
    UPLINK=$2
    rc=0

    # shape everything at $UPLINK speed - this prevents huge queues in your
    # DSL modem which destroy latency:
    tc class $STATUS dev $IFUP parent 1: classid 1:1 htb rate ${UPLINK}kbit burst 6k || rc=$?

    # high prio class 1:10:
    tc class $STATUS dev $IFUP parent 1:1 classid 1:10 htb rate ${UPLINK}kbit burst 6k prio 1 || rc=$?

    if test $FILTER -eq 1; then
        # bulk & default class 1:20 - gets slightly less traffic, and a lower priority:
        tc class $STATUS dev $IFUP parent 1:1 classid 1:20 htb rate $((9*$UPLINK/10))kbit burst 6k prio 2 || rc=$?
        tc class $STATUS dev $IFUP parent 1:1 classid 1:30 htb rate $((8*$UPLINK/10))kbit burst 6k prio 2 || rc=$?
    fi

    return $rc
}

mg_bw_down() {
    STATUS=$1
    DOWNLINK=$2
    rc=0

    tc class $STATUS dev $IFDOWN parent 1: classid 1:1 htb rate ${DOWNLINK}kbit burst 10k || rc=$?
    # high prio class 1:10:
    tc class $STATUS dev $IFDOWN parent 1:1 classid 1:10 htb rate ${DOWNLINK}kbit burst 10k prio 1 || rc=$?

    return $rc
}

# To be launched after having used 'start' method: mgbw add 1000 15000 => up: 1M
ch_bw() {
    UPLINK=$1
    DOWNLINK=$2
    echo -n "BW: $@ "
    rc=0
    # Upload
    mg_bw_up change $UPLINK || rc=$?
    # Download
    mg_bw_down change $DOWNLINK || rc=$?
    return $rc
}

start() {
    LIMIT_UP=$1
    shift
    LIMIT_DW=$1
    shift
    UPLINK=$1
    shift
    DOWNLINK=$1
    shift
    NETEM="$@"
    rc=0

    for i in $MODULES; do
        # hide/ignore errors
        modprobe $i > /dev/null
    done

    # From OpenWRT's WShaper script:
    ###### uplink

    # install root HTB, point default traffic to 1:20:
    test $FILTER -eq 1 && DEFAULT=20 || DEFAULT=10
    tc qdisc add dev $IFUP handle 1: root htb default $DEFAULT || rc=$?
    mg_bw_up add $UPLINK || rc=$?
    mg_netem_up add $LIMIT_UP $NETEM || rc=$?

    if test $FILTER -eq 1; then
        # TOS Minimum Delay (ssh, NOT scp) in 1:10:
        tc filter add dev $IFUP parent 1:0 protocol ip prio 10 u32 \
            match ip tos 0x10 0xff  flowid 1:10 || rc=$?

        # ICMP (ip protocol 1) in the interactive class 1:10 so we
        # can do measurements & impress our friends:
        tc filter add dev $IFUP parent 1:0 protocol ip prio 10 u32 \
            match ip protocol 1 0xff flowid 1:10 || rc=$?

        # To speed up downloads while an upload is going on, put ACK packets in
        # the interactive class:
        tc filter add dev $IFUP parent 1: protocol ip prio 10 u32 \
            match ip protocol 6 0xff \
            match u8 0x05 0x0f at 0 \
            match u16 0x0000 0xffc0 at 2 \
            match u8 0x10 0xff at 33 \
            flowid 1:10 || rc=$?
            # match:
            #  * u8: check by 8 bits
            #  * 0x10: value to be matched
            #  * 0xff: mask on which the previous value has to be matched => here, exactly match 0x10 ; if mask = 0x0f, only match last 4 bits.
            #  * at 33: at 33th byte since IP header start.
            # Here: protocol TCP, header length == 5 (20 bytes), max total length header 64 bytes and pure ACK.
            # source: http://lartc.org/howto/lartc.adv-filter.html

        # rest is 'non-interactive' ie 'bulk' and ends up in 1:20
        tc filter add dev $IFUP parent 1: protocol ip prio 18 u32 \
            match ip dst 0.0.0.0/0 flowid 1:20 || rc=$?
    fi


    ########## downlink #############
    tc qdisc add dev $IFDOWN handle 1: root htb default 10 || rc=$?
    mg_bw_down add $DOWNLINK || rc=$?
    mg_netem_down add $LIMIT_DW $NETEM || rc=$?
    return $rc
}

stop() {
    tc qdisc del dev $IFUP   root    2> /dev/null > /dev/null
    tc qdisc del dev $IFUP   ingress 2> /dev/null > /dev/null
    tc qdisc del dev $IFDOWN root    2> /dev/null > /dev/null
    tc qdisc del dev $IFDOWN ingress 2> /dev/null > /dev/null
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
    echo "Usage: $0 {start|stop|restart|show|netem|chbw} IFaceUp IFaceDw [limitUp limitDw [BWup BWdw] [netem rules]]"
    echo
    echo "  * IFaceUp / IFaceDw is the interface corresponding to uplink (wan) / downlink (lan)"
    echo "  * limitUp / limitDw is the netem limit's option for the uplink (wan) / downlink (lan): bandwidth (bytes/sec) * RTT/2 (sec)"
    echo "  * BWup / BWdw is the bandwidth allocated for the uplink (wan) / downlink (lan)"
    echo "  * netem rules: to add delay/losses but not rate/limit. See 'man netem'"
    echo
    echo "Examples:"
    echo "    ./$0 start eth0.2 wlan0 1750 13125 2000 15000"
    echo "    ./$0 start eth0.2 wlan0 13375 100312 2000 15000 delay 50ms 5ms loss 0.5% 25%"
    echo "                            limits       kbps kbps  netem"
    echo "    ./$0 netem eth0.2 wlan0 4625 34687 delay 15ms 2ms loss 0.05% 5%"
    echo "    ./$0 stop  eth0.2 wlan0"
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
    netem)
        echo -n "Change Netem rules: "
        test -z "$1" && echo "No netem args, exit" && exit 1
        netem $@ || exit $?
        echo "done"
    ;;
    chbw)
        echo -n "Change bandwidth: "
        test -z "$1" -o -z "$2" && echo "No up and down args, exit" && exit 1
        ch_bw $1 $2 || exit $?
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
