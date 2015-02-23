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

MODULES='sch_ingress sch_sfq sch_htb cls_u32 act_police ifb'

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
mgbw() {
    STATUS=$1
    shift
    echo "BW: $STATUS : $@"
    rc=0
    tc qdisc $STATUS dev $IF  parent 2:1 handle 10: tbf rate ${1}kbit buffer 3200 limit 6000 || rc=$?
    tc qdisc $STATUS dev ifb0 parent 1:1 handle 10: tbf rate ${2}kbit buffer 3200 limit 6000 || rc=$?
    return $rc
}

start() {
    BWU=$1
    shift
    BWD=$1
    shift
    NETEM="$@"

    for i in $MODULES; do
        modprobe $i > /dev/null
    done

    # Download: use virtual iface, redirect egress traffic to it
    rc=0
    ifconfig ifb0 up
    tc qdisc add dev $IF ingress || rc=$?
    tc filter add dev $IF parent ffff: protocol ip u32 match u32 0 0 flowid 1:1 action mirred egress redirect dev ifb0 || rc=$?

    test -n "$NETEM" && (mgnetem add $NETEM || rc=$?)
    mgbw add $BWU $BWD || rc=$?
    return $rc
}

stop() {
    for i in $MODULES; do
        modprobe $i > /dev/null
    done

    rc=0
    echo "Ingress"
    tc qdisc del dev $IF ingress || rc=$?
    echo "filter"
    tc filter del dev $IF parent ffff: || rc=$?
    echo "parents"
    tc qdisc del dev $IF parent 2:1 || rc=$?
    tc qdisc del dev eth0.2 parent 1:1 || rc=$?
    echo "root"
    tc qdisc del dev ifb0 root || rc=$?
    tc qdisc del dev $IF root || rc=$?

#    ifconfig ifb0 down # can be a problem

    # not needed
#    for i in $MODULES; do
#        rmmod $i
#    done
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
    echo "Download link:"
    tc -s qdisc ls dev ifb0

    echo "Upload link:"
    tc -s qdisc ls dev $IF
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
        mgbw change $1 $2 || exit $?
        echo "done"
    ;;
    *)
        echo "Usage: $0 {start|stop|restart|show|addnetem|chnetem|chbw} IFace [BWup BWdw [netem rules]] [netem rules]"
    ;;
esac

exit 0
