#! /usr/bin/python3
# -*- coding: utf-8 -*-
#
#  Copyright 2014-2015 Matthieu Baerts & Quentin De Coninck
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.

# Goal: launch uitests with TCP, MPTCP and MPTCP FullMesh only with both WLAN
#       and RMNET interfaces and add delay/losses during each uitest

import os
import time

import lt_network as net

from lt_utils import *

CTRL_WIFI = True

if os.path.isfile('launch_tests_conf.py'):
    from launch_tests_conf import *

# Out in another dir
OUTPUT_DIR = '~/Thesis/TCPDump_bad_simulation'

# Only both4: we will modify the router during the tests
NETWORK_TESTS = 'both4'

# Do not Enable Android's Wi-Fi option, we will simulate it
AVOID_POOR_CONNECTIONS = False
# Take 3 time more
LAUNCH_UITESTS_ARGS = 'mult-time 3'
TIMEOUT = 60*3 *3

# Tests with ShadowSocks, with SSHTunnel, it will try to reconnect each time the connection change
WITH_SSH_TUNNEL = False
WITH_SHADOWSOCKS = True

# Tests with all modes:
WITH_TCP = True # we should see deconnections => bad perf
WITH_MPTCP = True # we should see switch
WITH_FULLMESH = True # a bit better if we start the connection with the best one

CHANGE_CASE = 'loss' # or 'delay' or 'both' (loss + delay)
CHANGE_SWITCH = 10 # after 10 iters
CHANGE_LIMIT = 20 # max 20 iters
CHANGE_INC = 1 # +1 after each iter (e.g. +5 for the delay)
CHANGE_INC_BOTH_DELAY = 5 # if 'both', increment of 5*INC for the delay
CHANGE_TIME = 15 # WAIT 15sec before the next iter
CHANGE_METHOD = 'wifi' # or 'route' or 'prefer' or 'ip'
# route: change the default route to wlan/rmnet but it will only affect new connections.
# prefer: used `svc wifi|data prefer`: will switch to wlan/rmnet but it will disable the other one (until the one which is used is disabled).
# wifi: will disable/enable wifi. Then it should switch to rmnet and re-used Wi-Fi only when wlan is enabled AND connected.
# ip: will use iproute2: ip link set dev eth0 multipath off

THREAD_CONTINUE = True
def func_init(app, net_name, mptcp_dir, out_dir):
    global THREAD_CONTINUE
    THREAD_CONTINUE = True

# we have ~4.5 minutes: inc losses/delay every 15 sec
def func_start(app, net_name, mptcp_dir, out_dir):
    global THREAD_CONTINUE, CHANGE_CASE, CHANGE_SWITCH, CHANGE_INC, CHANGE_INC_BOTH_DELAY, CHANGE_TIME, CHANGE_METHOD

    i = CHANGE_INC
    while True:
        time.sleep(CHANGE_TIME)
        if not THREAD_CONTINUE: return

        if i == CHANGE_INC:
            net.enable_netem_var(CHANGE_CASE, i, i * CHANGE_INC_BOTH_DELAY)
        else:
            net.change_netem_var(CHANGE_CASE, i, i * CHANGE_INC_BOTH_DELAY)

        # prefer Data over Wi-Fi
        if i == CHANGE_SWITCH * CHANGE_INC:
            # forcer changement avec MPTCP: voir sysctl? stop wifi? net.disable_iface(net.WIFI)
            if CHANGE_METHOD == 'route' and mptcp_dir.startswith('MPTCP'):
                success = net.change_default_route_rmnet()
            elif CHANGE_METHOD == 'prefer':
                success = net.prefer_iface(net.RMNET)
            elif CHANGE_METHOD == 'ip' and mptcp_dir.startswith('MPTCP'):
                success = iproute_set_multipath_backup_wlan()
            else:
                success = net.disable_iface(net.WIFI)
            if not success:
                my_print_err("Not able to switch with method " + CHANGE_METHOD)
        elif i == CHANGE_LIMIT * CHANGE_INC:
            return
        i += CHANGE_INC


def func_end(app, net_name, mptcp_dir, out_dir, success):
    global THREAD_CONTINUE, CHANGE_METHOD
    THREAD_CONTINUE = False

    if CHANGE_METHOD == 'route' and mptcp_dir.startswith('MPTCP'):
        rc = net.change_default_route_wlan()
    elif CHANGE_METHOD == 'prefer':
        rc = net.prefer_iface(net.WLAN)
        # 'svc data prefer' cmd will disable WLAN, we need to enable both ifaces
        # relaunch multipath_control
        if mptcp_dir == 'MPTCP':
            rc &= net.multipath_control("enable")
        elif mptcp_dir == 'MPTCP_FM':
            rc &= net.multipath_control("enable", path_mgr="fullmesh")
    elif CHANGE_METHOD == 'ip' and mptcp_dir.startswith('MPTCP'):
        rc = iproute_set_multipath_backup_rmnet()
    else: # wifi
        rc = net.enable_iface(net.WIFI)

    if not rc:
        my_print_err("Not able to return to init state with method " + CHANGE_METHOD)

    net.disable_netem()

def func_exit(app, net_name, mptcp_dir, out_dir, thread):
    # Wait for the end of the thread: avoid
    if thread and thread.is_alive():
        my_print("Wait the end of the thread")
        thread.join(timeout=CHANGE_TIME+1)
        if thread.is_alive():
            my_print_err("Thread is still alive for " + app + " - " + net_name)

# Functions that can be launched just before/after each uitest
LAUNCH_FUNC_INIT = func_init
LAUNCH_FUNC_START = func_start
LAUNCH_FUNC_END = func_end
LAUNCH_FUNC_EXIT = func_exit

if os.path.isfile('launch_tests_conf_bad_simulation_custom.py'):
    from launch_tests_conf_bad_simulation_custom import *

if not CTRL_WIFI:
    my_print_err("We need to control Wi-Fi for these tests...")
    from sys import exit
    exit(1)
