#!/bin/sh
#
# With the help of Nicolargo's limitbw script and OpenWRT's WShaper tool:
# limitbw: http://blog.nicolargo.com/2009/03/simuler-un-lien-wan-sous-linux.html
#
#     ./shaper.sh ACTION IF [BWup BWdw [netem rules]]
#
# e.g.: ./shaper.sh start   eth0.2 2000 15000 delay 50ms 5ms loss 0.5% 25%
#                                  kbps kbps
#       ./shaper.sh chnetem eth0.2 delay 15ms 2ms loss 0.05% 5%
#       ./shaper.sh stop    eth0.2

test -n "$1" && ACTION=$1 && shift || ACTION='help'
# Interface name (e.g. eth0.2)
test -n "$1" && IF=$1 && shift || ACTION='help'

MODULES='sch_ingress sch_sfq sch_htb cls_u32 act_police'

# To be launched after having used 'start' method
mgnetem() {
    STATUS=$1
    shift
    echo "Netem: $STATUS : $@"
    rc=0
    tc qdisc $STATUS dev ifb0 root handle 1:0 netem $@ || rc=$?
    tc qdisc $STATUS dev $IF  root handle 2:0 netem $@ || rc=$?
    return $rc
}

# To be launched after having used 'start' method: mgbw add 1000 15000 => up: 1M
chbw() {
    UPLINK=$1
    DOWNLINK=$2
    echo "BW: $@"
    rc=0
    tc class change dev $IF parent 1:  classid 1:1  htb rate ${UPLINK}kbit burst 6k || rc=$?
    tc class change dev $IF parent 1:1 classid 1:10 htb rate ${UPLINK}kbit burst 6k prio 1 || rc=$?
    tc class change dev $IF parent 1:1 classid 1:20 htb rate $((9*$UPLINK/10))kbit burst 6k prio 2 || rc=$?
    tc class change dev $IF parent 1:1 classid 1:30 htb rate $((8*$UPLINK/10))kbit burst 6k prio 2 || rc=$?
    tc filter change dev $IF parent ffff: protocol ip prio 50 u32 match ip src \
       0.0.0.0/0 police rate ${DOWNLINK}kbit burst 10k drop flowid :1 || rc=$?
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
    tc qdisc add dev $IF root handle 1: htb default 20

    # shape everything at $UPLINK speed - this prevents huge queues in your
    # DSL modem which destroy latency:
    tc class add dev $IF parent 1: classid 1:1 htb rate ${UPLINK}kbit burst 6k

    # high prio class 1:10:
    tc class add dev $IF parent 1:1 classid 1:10 htb rate ${UPLINK}kbit burst 6k prio 1

    # bulk & default class 1:20 - gets slightly less traffic, and a lower priority:
    tc class add dev $IF parent 1:1 classid 1:20 htb rate $((9*$UPLINK/10))kbit burst 6k prio 2
    tc class add dev $IF parent 1:1 classid 1:30 htb rate $((8*$UPLINK/10))kbit burst 6k prio 2

    # all get Stochastic Fairness:
    tc qdisc add dev $IF parent 1:10 handle 10: sfq perturb 10
    tc qdisc add dev $IF parent 1:20 handle 20: sfq perturb 10
    tc qdisc add dev $IF parent 1:30 handle 30: sfq perturb 10

    # TOS Minimum Delay (ssh, NOT scp) in 1:10:
    tc filter add dev $IF parent 1:0 protocol ip prio 10 u32 \
          match ip tos 0x10 0xff  flowid 1:10

    # ICMP (ip protocol 1) in the interactive class 1:10 so we
    # can do measurements & impress our friends:
    tc filter add dev $IF parent 1:0 protocol ip prio 10 u32 \
            match ip protocol 1 0xff flowid 1:10

    # To speed up downloads while an upload is going on, put ACK packets in
    # the interactive class:
    tc filter add dev $IF parent 1: protocol ip prio 10 u32 \
       match ip protocol 6 0xff \
       match u8 0x05 0x0f at 0 \
       match u16 0x0000 0xffc0 at 2 \
       match u8 0x10 0xff at 33 \
       flowid 1:10

    # rest is 'non-interactive' ie 'bulk' and ends up in 1:20
    tc filter add dev $IF parent 1: protocol ip prio 18 u32 \
       match ip dst 0.0.0.0/0 flowid 1:20


    ########## downlink #############
    # slow downloads down to somewhat less than the real speed  to prevent
    # queuing at our ISP. Tune to see how high you can set it.
    # ISPs tend to have *huge* queues to make sure big downloads are fast
    #
    # attach ingress policer:
    tc qdisc add dev $IF handle ffff: ingress

    # filter *everything* to it (0.0.0.0/0), drop everything that's
    # coming in too fast:
    tc filter add dev $IF parent ffff: protocol ip prio 50 u32 match ip src \
       0.0.0.0/0 police rate ${DOWNLINK}kbit burst 10k drop flowid :1

    # test -n "$NETEM" && (mgnetem add $NETEM || rc=$?)
    # mgbw add $UPLINK $DOWNLINK || rc=$?
    #return $rc
}

stop() {
    tc qdisc del dev $IF root    2> /dev/null > /dev/null
    tc qdisc del dev $IF ingress 2> /dev/null > /dev/null
    ## not needed?
    # for i in $MODULES; do
    #     rmmod $i
    # done
    return $rc
}

restart() {
    rc=0
    stop || rc=$?
    sleep 1
    start $@ || rc=$?
    return $rc
}

show() {
    tc -s qdisc ls dev $IF
    tc -s class ls dev $IF
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
        mgnetem add $@ || exit $?
        echo "done"
    ;;
    chnetem)
        echo -n "Change Netem rules: "
        test -z "$1" && echo "No netem args, exit" && exit 1
        mgnetem change $@ || exit $?
        echo "done"
    ;;
    chbw)
        echo -n "Change bandwidth: "
        test -z "$1" -o -z "$2" && echo "No up and down args, exit" && exit 1
        chbw $1 $2 || exit $?
        echo "done"
    ;;
    *)
        echo "Usage: $0 {start|stop|restart|show|addnetem|chnetem|chbw} IFace [BWup BWdw [netem rules]] [netem rules]"
    ;;
esac

exit 0
