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
#
# ./launch_tests.py [CONFIG_FILE.py]
#
# To install on this machine: ant, adb, android, sshpass
# Don't forget to load your SSH key for backup_traces.sh script!

import os
import random
import shutil # rmtree
import subprocess
import sys
import time

from enum import Enum

import lt_globals
lt_globals.init()

from lt_settings import * # config

from lt_device   import *
from lt_network  import *

from lt_utils import *


##################################################
##            MACHINE: PREPARE TESTS            ##
##################################################

os.chdir(s.ROOT_DIR)

cmd = "git describe --abbrev=0 --dirty --always"
git_rev = subprocess.check_output(cmd.split(), universal_newlines=True).splitlines()[0]
my_print("Git version: " + git_rev)

my_print("Starting tests " + time.ctime())
now_dir = time.strftime("%Y%m%d-%H%M%S") + "_" + git_rev

# Prepare output dir
arg_dir_exp = os.path.expanduser(OUTPUT_DIR)
output_dir = os.path.join(arg_dir_exp, now_dir)
if (not os.path.isdir(output_dir)):
    os.makedirs(output_dir)
my_print("Save tcpdump files in " + output_dir)
print("\n======================================\n\n")

# should start with uitests, not an exception and with build.xml file
def is_valid_uitest(ui_dir):
    if not ui_dir.startswith('uitests-'):
        return False
    if ui_dir in UITESTS_EXCEPTIONS or ui_dir in UITESTS_BLACKLIST:
        return False
    return os.path.isfile(os.path.join(ui_dir, 'build.xml'))

# Get list of uitest dir (should contain build.xml file)
uitests_dir = []
if RESTRICT_UITESTS: # only do some tests
    uitests_dir = RESTRICT_UITESTS
    my_print("Restrict to these tests: " + str(uitests_dir))
else:
    for file in os.listdir('.'):
        if is_valid_uitest(file):
            uitests_dir.append(file)

if RESTRICT_UITESTS_NB: # limit nb of uitests
    random.shuffle(uitests_dir)
    uitests_dir = uitests_dir[:RESTRICT_UITESTS_NB]
    my_print("Restrict to " + RESTRICT_UITESTS_NB + " tests: " + str(uitests_dir))

# Prepare the tests (build the jar if needed)
for uitest in uitests_dir + UITESTS_EXCEPTIONS:
    app = uitest[8:]
    my_print("Checking requirements for " + app)
    need_creation = DEVEL or not os.path.isfile(os.path.join(uitest, 'local.properties'))
    # Create project if needed
    if need_creation:
        my_print("Creating uitest-project")
        cmd = "android create uitest-project -n " + uitest + " -t 1 -p " + uitest
        if subprocess.call(cmd.split()) != 0:
            my_print_err("when creating uitest-project for " + app)
            continue

    # Build project and push jar if needed
    jar_file = os.path.join(uitest, 'bin', uitest + '.jar')
    if need_creation or not os.path.isfile(jar_file):
        my_print("Build ant and push jar")
        os.chdir(uitest)

        # remove bin dir
        if os.path.isdir('bin'):
            shutil.rmtree('bin')

        cmd = "ant build"
        rt = subprocess.call(cmd.split())
        os.chdir(root_dir)
        if rt != 0:
            my_print_err("when building jar for " + app)
            continue

        # push the new jar
        cmd = "adb push " + jar_file + " " + ANDROID_HOME + "/" + uitest + ".jar"
        if subprocess.call(cmd.split()) != 0:
            my_print_err("when pushing jar for " + app)
            continue

print("\n======================================\n\n")


##################################################
##            ROUTER: PREPARE TESTS             ##
##################################################

# Check router OK and insert mod + delete rules
if CTRL_WIFI:
    my_print("Checking router connexion")
    if (not router_shell("echo OK")):
        my_print_err("Not able to be connected to the router, exit")
        exit(1)
    my_print("Reset Netem (tc), ignore errors")
    router_shell("insmod /lib/modules/3.3.8/sch_netem.ko")
    disable_netem()


##################################################
##            DEVICE: PREPARE TESTS             ##
##################################################

adb_restart()

my_print("Check device is up")
for i in range(5): # check 5 time, max 30sec: should be enough
    adb_check_reboot()
    if lt_globals.LAST_UPTIME:
        break
    time.sleep(6)

if not lt_globals.LAST_UPTIME:
    my_print_err("Not able to contact the device... Stop")
    sys.exit(1)

if PURGE_TRACES_SMARTPHONE:
    my_print("Remove previous traces located on the phone")
    adb_shell("rm -r " + ANDROID_TRACE_OUT + "*")

# remove sim if any to launch the first UiTest
adb_check_reboot_sim()

# Wi-Fi option
avoid_poor_connections(AVOID_POOR_CONNECTIONS)

if WITH_SHADOWSOCKS:
    my_print("Using ShadowSocks:")
    if SSH_TUNNEL_INSTALLED:
        my_print("stop + kill SSHTunnel")
        # Stop + kill ssh_tunnel
        adb_shell(False, uiautomator='ssh_tunnel', args='action stopnotautoconnect')
        adb_shell_root("am force-stop org.sshtunnel")
    my_print("start + autoconnect ShadowSocks")
    # Start shadown socks with autoconnect (in case of random reboot)
    if not adb_shell(False, uiautomator='shadow_socks', args='action startautoconnect'):
        my_print_err('Not able to start shadowsocks... Stop')
        sys.exit(1)
elif WITH_SSH_TUNNEL:
    if SHADOWSOCKS_INSTALLED:
        my_print("Using SSHTunnel: stop + kill ShadowSocks")
        # Stop + kill ShadowSocks
        adb_shell(False, uiautomator='shadow_socks', args='action stopnotautoconnect')
        adb_shell_root("am force-stop com.github.shadowsocks")
    my_print("start + autoconnect sshtunnel")
    # Start shadown socks with autoconnect (in case of random reboot)
    if not adb_shell(False, uiautomator='ssh_tunnel', args='action startautoconnect'):
        my_print_err('Not able to start sshtunnel... Stop')
        sys.exit(1)


# Should start with wlan/bothX/rmnetX
Network = Enum('Network', NETWORK_TESTS)

mptcp = []
if WITH_MPTCP:
    mptcp.append('MPTCP')
if WITH_TCP:
    mptcp.append('TCP')
if WITH_FULLMESH:
    mptcp.append('MPTCP_FM')
random.shuffle(mptcp)

lt_globals.TEST_NO = 1
lt_globals.NB_TESTS = len(Network) * len(mptcp) * len(uitests_dir)


##################################################
##             DEVICE: LAUNCH TESTS             ##
##################################################

for mptcp_dir in mptcp:
    my_print("============ Kernel mode: " + mptcp_dir + " =========\n")

    # All kinds of networks
    net_list = list(Network)
    random.shuffle(net_list)
    my_print("Network list:")
    print(*(net.name for net in net_list))

    for net in net_list:
        name = net.name
        my_print("========== Network mode: " + name + " ===========\n")

        # Reboot the device: avoid bugs...
        my_print("Reboot the phone: avoid possible bugs")
        if not adb_reboot():
            continue
        if mptcp_dir == 'MPTCP':
            multipath_control("enable")
        elif mptcp_dir == 'MPTCP_FM':
            multipath_control("enable", path_mgr="fullmesh")
        else:
            multipath_control("disable")

        # Check if we need to simulate errors
        tc = False
        index = name.find('TC')
        if index >= 0:
            if not CTRL_WIFI:
                my_print_err('We do not control the WiFi router, skip this test')
                continue
            tc = name[index+2:]
            name = name[0:index]

        # Network of the device
        if name == 'wlan': # net == Network.wlan: cannot use this dynamic enum
            enable_iface(WIFI)
            disable_iface(DATA)
        # elif name == 'both4Data': # net == Network.both4Data: # prefer data
        #     both('4', prefer_wifi=False)
        elif name.startswith('both'):
            both(name[4])
        elif name.startswith('rmnet'):
            rmnet(name[5])
        else:
            my_print_err('unknown: SKIP')
            continue

        my_print("Wait 5 seconds and restart proxy")
        time.sleep(5)

        # Network of the router
        if tc:
            # Losses
            netem = loss_cmd(get_value_between(tc, 'L', 'p'))
            # Delay
            netem += delay_cmd(get_value_between(tc, 'D', 'm'))
            if netem:
                enable_netem(netem)

        # Launch test
        launch_all(uitests_dir, net.name, mptcp_dir, output_dir, LAUNCH_FUNC_START, LAUNCH_FUNC_END, LAUNCH_UITESTS_ARGS)

        # Delete Netem
        if tc:
            disable_netem()

my_print("================ DONE =================\n")


##################################################
##                DEVICE: CLEAN                 ##
##################################################

if PURGE_TRACES_SMARTPHONE:
    my_print("Remove traces located on the phone")
    adb_shell("rm -r " + ANDROID_TRACE_OUT + "*")


my_print("Reboot the phone") # to avoid possible Android bugs
adb_reboot(wait=False)


##################################################
##                MACHINE: CLEAN                ##
##################################################

# backup traces
my_print("Backup traces") # better to backup files
cmd = "bash backup_traces.sh " + arg_dir_exp
if BACKUP_TRACES and subprocess.call(cmd.split()) != 0:
    my_print_err(" when using backup_traces.sh with " + arg_dir_exp)

if KEEP_TRACES_NB:
    dirs = sorted(os.listdir(arg_dir_exp), reverse=True)
    for rm_dir in dirs[KEEP_TRACES_NB:]:
        my_print("Remove previous traces: " + rm_dir)
        shutil.rmtree(os.path.join(arg_dir_exp, rm_dir))
