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
#       and RMNET interfaces and wait before launching the next uitest

import os

import lt_device as dev

from lt_utils import * # my_print

CTRL_WIFI = False # we will switch between APs, not possible to control them
YELLOWB   = "\033[1;33m"
WHITE_STD = "\033[0;39m"

if os.path.isfile('launch_tests_conf.py'):
    from launch_tests_conf import *

# Out in another dir
OUTPUT_DIR = '~/Thesis/TCPDump_move_2_AP'

# Only both4: we will modify the router during the tests
NETWORK_TESTS = 'both4' # both3 ?
# Limit Bandwidth: (up, down) ; ex: VDSL: (20000, 40000)
LIMIT_BW = (1000, 15000) # can be interested but we need to be able to contact router at the beginning end/script
LIMIT_BW_WSHAPER_SUPPORTED = True

# Do not Enable Android's Wi-Fi option
AVOID_POOR_CONNECTIONS_TCP = False
AVOID_POOR_CONNECTIONS_MPTCP = False
# Tests with ShadowSocks, with SSHTunnel, it will try to reconnect each time the connection change
WITH_SSH_TUNNEL = False
WITH_SHADOWSOCKS = True

# Tests with all modes:
WITH_TCP = True # we should see deconnections => bad perf
WITH_MPTCP = False # not needed when not using extra subflow
WITH_MPTCP_FULLMESH = True # a bit better if we start the connection with the best one
WITH_MPTCP_FULLMESH_ROUND_ROBIN = False # can be useful only to see what happens
WITH_MPTCP_BACKUP = True # should be the default behaviour
WITH_MPTCP_NDIFFPORTS = False # can be interesting to use several subflows when having losses

THREAD_CONTINUE = True
def func_init(app, net_name, tcp_mode, out_dir):
    global THREAD_CONTINUE
    THREAD_CONTINUE = True


def func_start(app, net_name, tcp_mode, out_dir):
    """ log signal power """
    global THREAD_CONTINUE

    log_wlan  = open(os.path.join(out_dir, app, 'signal-wlan.csv'), 'w')
    log_rmnet = open(os.path.join(out_dir, app, 'signal-rmnet.csv'), 'w')

    print(dev.get_info_wifi_power_header(),  file=log_wlan)
    print(dev.get_info_rmnet_power_header(), file=log_rmnet)

    while True:
        print(dev.get_info_wifi_power(),  file=log_wlan)
        print(dev.get_info_rmnet_power(), file=log_rmnet)
        time.sleep(1)
        if not THREAD_CONTINUE:
            break

    log_wlan.close()
    log_rmnet.close()

def func_end(app, net_name, tcp_mode, out_dir, success):
    global THREAD_CONTINUE
    THREAD_CONTINUE = False

def func_exit(app, net_name, tcp_mode, out_dir, thread):
    # Wait for the end of the thread
    if thread and thread.is_alive():
        my_print("Wait the end of the thread")
        thread.join(timeout=5)
        if thread.is_alive():
            my_print_err("Thread is still alive for " + app + " - " + net_name)

    input(YELLOWB + "\n\nEnd for " + app + " in " + net_name + " with " +
          tcp_mode + ".\nPress Enter to launch the next one: " +
          "be sure that you're connected to the network\n\n" + WHITE_STD)

LAUNCH_FUNC_INIT = func_init
LAUNCH_FUNC_START = func_start
LAUNCH_FUNC_END = func_end
LAUNCH_FUNC_EXIT = func_exit

if os.path.isfile('launch_tests_conf_move_2_AP_custom.py'):
    from launch_tests_conf_move_2_AP_custom import *

if LIMIT_BW and len(IP_ROUTER) < 2:
    my_print_err("Only control one router, is it normal?")
