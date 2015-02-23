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
    tc qdisc $STATUS dev ifb0 root handle 1:0 netem $@
    tc qdisc $STATUS dev $IF  root handle 2:0 netem $@
}

# To be launched after having used 'start' method: mgbw add 1000 15000 => up: 1M
mgbw() {
    STATUS=$1
    shift
    echo "BW: $STATUS : $@"
    tc qdisc $STATUS dev $IF  parent 2:1 handle 10: tbf rate ${1}kbit buffer 3200 limit 6000
    tc qdisc $STATUS dev ifb0 parent 1:1 handle 10: tbf rate ${2}kbit buffer 3200 limit 6000
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
    ifconfig ifb0 up
    tc qdisc add dev $IF ingress
    tc filter add dev $IF parent ffff: protocol ip u32 match u32 0 0 flowid 1:1 action mirred egress redirect dev ifb0

    test -n "$NETEM" && mgnetem add $NETEM
    mgbw add $BWU $BWD
}

stop() {
    for i in $MODULES; do
        modprobe $i > /dev/null
    done

    echo "Ingress"
    tc qdisc del dev $IF ingress
    echo "filter"
    tc filter del dev $IF parent ffff:
    echo "parents"
    tc qdisc del dev $IF parent 2:1
    tc qdisc del dev eth0.2 parent 1:1
    echo "root"
    tc qdisc del dev ifb0 root
    tc qdisc del dev $IF root

#    ifconfig ifb0 down # can be a problem

    # not needed
#    for i in $MODULES; do
#        rmmod $i
#    done
}

restart() {
    stop
    sleep 1
    start $@
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
        start $@
        echo "done"
    ;;
    stop)
        echo -n "Stopping shaping rules: "
        stop
        echo "done"
    ;;
    restart)
        echo -n "Restarting shaping rules: "
        test -z "$1" -o -z "$2" && echo "No up and down args, exit" && exit 1
        restart $@
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
        mgnetem add $@
        echo "done"
    ;;
    chnetem)
        echo -n "Change Netem rules: "
        test -z "$1" && echo "No netem args, exit" && exit 1
        mgnetem change $@
        echo "done"
    ;;
    chbw)
        echo -n "Change bandwidth: "
        test -z "$1" -o -z "$2" && echo "No up and down args, exit" && exit 1
        mgbw change $1 $2
        echo "done"
    ;;
    *)
        echo "Usage: $0 {start|stop|restart|show|addnetem|chnetem|chbw} IFace [BWup BWdw [netem rules]] [netem rules]"
    ;;
esac

exit 0
