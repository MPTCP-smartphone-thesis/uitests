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

# Tests with ShadowSocks
WITH_SSH_TUNNEL = False
WITH_SHADOWSOCKS = True

# Tests with all modes:
WITH_TCP = True # we should see deconnections => bad perf
WITH_MPTCP = True # we should see switch
WITH_FULLMESH = True # a bit better if we start the connection with the best one

CHANGE_CASE = 'loss' # or 'delay' or 'both'
CHANGE_SWITCH = 10 # after 10 iters
CHANGE_INC = 1 # +1 after each iter (e.g. +5 for the delay)
CHANGE_INC_BOTH_DELAY = 5 # if 'both', increment of 5*INC for the delay
CHANGE_TIME = 15 # WAIT 15sec before the next iter

THREAD_CONTINUE = True
# we have ~4.5 minutes: inc losses/delay every 15 sec
def func_start(app, net, mptcp_dir, out_dir):
    global THREAD_CONTINUE, CHANGE_CASE, CHANGE_SWITCH, CHANGE_INC, CHANGE_INC_BOTH_DELAY, CHANGE_TIME
    THREAD_CONTINUE = True
    wlan,rmnet = net.get_all_ipv4()
    net.change_default_route(net.WLAN, wlan)

    i = CHANGE_INC

    while True:
        time.sleep(CHANGE_TIME)
        if THREAD_CONTINUE: return
        if i == CHANGE_INC:
            net.enable_netem_var(CHANGE_CASE, i, i * CHANGE_INC_BOTH_DELAY)
        else:
            net.change_netem_var(CHANGE_CASE, i, i * CHANGE_INC_BOTH_DELAY)

        # prefer Data over Wi-Fi
        if i == CHANGE_SWITCH * CHANGE_INC:
            net.change_default_route(net.RMNET, rmnet)
        i += CHANGE_INC


def func_end(app, net, mptcp_dir, out_dir, success):
    global THREAD_CONTINUE
    THREAD_CONTINUE = False
    net.disable_netem()

# Functions that can be launched just before/after each uitest
LAUNCH_FUNC_START = func_start
LAUNCH_FUNC_END = func_end

if os.path.isfile('launch_tests_conf_bad_simulation_custom.py'):
    from launch_tests_conf_bad_simulation_custom import *

if not CTRL_WIFI:
    my_print_err("We need to control Wi-Fi for these tests...")
    from sys import exit
    exit(1)
