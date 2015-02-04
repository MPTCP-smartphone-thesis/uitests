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

# force to be in the right dir
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT_DIR)

import lt_globals as g
g.init()

import lt_settings as s # config
s.init()

import lt_device as dev
import lt_network as net

from lt_tcp import TCP
from lt_utils import *


##################################################
##            MACHINE: PREPARE TESTS            ##
##################################################

cmd = "git describe --abbrev=0 --dirty --always"
git_rev = subprocess.check_output(cmd.split(), universal_newlines=True).splitlines()[0]
my_print("Git version: " + git_rev)

my_print("Starting tests " + time.ctime())
now_dir = time.strftime("%Y%m%d-%H%M%S") + "_" + git_rev

# Prepare output dir
arg_dir_exp = os.path.expanduser(s.OUTPUT_DIR)
output_dir = os.path.join(arg_dir_exp, now_dir)
if (not os.path.isdir(output_dir)):
    os.makedirs(output_dir)
my_print("Save tcpdump files in " + output_dir)
print("\n======================================\n\n")

with open(os.path.join(output_dir, 'settings.cfg'), "w") as cfg_file:
    s.print_vars(file=cfg_file)

# should start with uitests, not an exception and with build.xml file
def is_valid_uitest(ui_dir):
    if not ui_dir.startswith('uitests-'):
        return False
    if ui_dir in s.UITESTS_EXCEPTIONS or ui_dir in s.UITESTS_BLACKLIST:
        return False
    return os.path.isfile(os.path.join(ui_dir, 'build.xml'))

# Get list of uitest dir (should contain build.xml file)
uitests_dir = []
if s.RESTRICT_UITESTS: # only do some tests
    uitests_dir = s.RESTRICT_UITESTS
    my_print("Restrict to these tests: " + str(uitests_dir))
else:
    for file in os.listdir('.'):
        if is_valid_uitest(file):
            uitests_dir.append(file)

if s.RESTRICT_UITESTS_NB: # limit nb of uitests
    random.shuffle(uitests_dir)
    uitests_dir = uitests_dir[:s.RESTRICT_UITESTS_NB]
    my_print("Restrict to " + s.RESTRICT_UITESTS_NB + " tests: " + str(uitests_dir))

# Prepare the tests (build the jar if needed)
for uitest in uitests_dir + s.UITESTS_EXCEPTIONS:
    app = uitest[8:]
    my_print("Checking requirements for " + app)
    need_creation = s.DEVEL or not os.path.isfile(os.path.join(uitest, 'local.properties'))
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
        os.chdir(ROOT_DIR)
        if rt != 0:
            my_print_err("when building jar for " + app)
            continue

        # push the new jar
        cmd = "adb push " + jar_file + " " + s.ANDROID_HOME + "/" + uitest + ".jar"
        if subprocess.call(cmd.split()) != 0:
            my_print_err("when pushing jar for " + app)
            continue

print("\n======================================\n\n")


##################################################
##            ROUTER: PREPARE TESTS             ##
##################################################

# Check router OK and insert mod + delete rules
if s.CTRL_WIFI:
    my_print("Checking router connexion")
    if (not net.router_shell("echo OK")):
        my_print_err("Not able to be connected to the router, exit")
        exit(1)
    my_print("Limit Bandwidth")
    if s.LIMIT_BW_WSHAPER_SUPPORTED:
        if s.LIMIT_BW:
            net.limit_bw_wshaper(s.LIMIT_BW[0], s.LIMIT_BW[1])
        else:
            net.unlimit_bw_wshaper()
    my_print("Reset Netem (tc), ignore errors")
    net.disable_netem()
    net.set_wlan_power('auto')


##################################################
##            DEVICE: PREPARE TESTS             ##
##################################################

dev.adb_restart()

my_print("Check device is up")
for i in range(5): # check 5 time, max 30sec: should be enough
    dev.adb_check_reboot()
    if g.LAST_UPTIME:
        break
    time.sleep(6)

if not g.LAST_UPTIME:
    my_print_err("Not able to contact the device... Stop")
    sys.exit(1)

if s.PURGE_TRACES_SMARTPHONE:
    my_print("Remove previous traces located on the phone")
    dev.adb_shell("rm -r " + s.ANDROID_TRACE_OUT + "*")

# remove sim if any to launch the first UiTest
dev.adb_check_reboot_sim()

if s.WITH_SHADOWSOCKS:
    my_print("Using ShadowSocks:")
    if s.SSH_TUNNEL_INSTALLED:
        my_print("stop + kill SSHTunnel")
        # Stop + kill ssh_tunnel
        dev.adb_shell(False, uiautomator='ssh_tunnel', args='action stopnotautoconnect')
        dev.adb_shell_root("am force-stop org.sshtunnel")
    my_print("start + autoconnect ShadowSocks")
    # Start shadown socks with autoconnect (in case of random reboot)
    if not dev.adb_shell(False, uiautomator='shadow_socks', args='action startautoconnect'):
        my_print_err('Not able to start shadowsocks... Stop')
        sys.exit(1)
elif s.WITH_SSH_TUNNEL:
    if s.SHADOWSOCKS_INSTALLED:
        my_print("Using SSHTunnel: stop + kill ShadowSocks")
        # Stop + kill ShadowSocks
        dev.adb_shell(False, uiautomator='shadow_socks', args='action stopnotautoconnect')
        dev.adb_shell_root("am force-stop com.github.shadowsocks")
    my_print("start + autoconnect sshtunnel")
    # Start shadown socks with autoconnect (in case of random reboot)
    if not dev.adb_shell(False, uiautomator='ssh_tunnel', args='action startautoconnect'):
        my_print_err('Not able to start sshtunnel... Stop')
        sys.exit(1)


# Should start with wlan/bothX/rmnetX
Network = Enum('Network', s.NETWORK_TESTS)

tcp_list = []
if s.WITH_TCP:
    tcp_list.append(TCP.TCP)
if s.WITH_MPTCP:
    tcp_list.append(TCP.MPTCP)
if s.WITH_MPTCP_FULLMESH:
    tcp_list.append(TCP.MPTCP_FULLMESH)
if s.WITH_MPTCP_FULLMESH_ROUND_ROBIN:
    tcp_list.append(TCP.MPTCP_FULLMESH_RR)
if s.WITH_MPTCP_BACKUP:
    tcp_list.append(TCP.MPTCP_BACKUP)
if s.WITH_MPTCP_NDIFFPORTS:
    tcp_list.append(TCP.MPTCP_NDIFFPORTS)
random.shuffle(tcp_list)

g.TEST_NO = 1
g.NB_TESTS = len(Network) * len(tcp_list) * len(uitests_dir)


##################################################
##             DEVICE: LAUNCH TESTS             ##
##################################################

for tcp_mode in tcp_list:
    my_print("============ Kernel mode: " + str(tcp_mode) + " =========\n")

    # All kinds of networks
    net_list = list(Network)
    random.shuffle(net_list)
    my_print("Network list:")
    print(*(net_mode.name for net_mode in net_list))

    for net_mode in net_list:
        name = net_mode.name
        my_print("========== Network mode: " + name + " ===========\n")

        # Reboot the device: avoid bugs...
        my_print("Reboot the phone: avoid possible bugs")
        if not dev.adb_reboot():
            continue

        # Check if we need to simulate errors
        tc = False
        index = name.find('TC')
        if index >= 0:
            if not s.CTRL_WIFI:
                my_print_err('We do not control the WiFi router, skip this test')
                continue
            tc = name[index+2:]
            name = name[0:index]

        # Network of the device
        if name == 'wlan': # net_mode == Network.wlan: cannot use this dynamic enum
            net.enable_iface(net.WIFI)
            net.disable_iface(net.DATA)
        # elif name == 'both4Data': # net_mode == Network.both4Data: # prefer data
        #     both('4', prefer_wifi=False)
        elif name.startswith('both'):
            net.both(name[4])
            if tcp_mode.is_mptcp():
                net.avoid_poor_connections(s.AVOID_POOR_CONNECTIONS_MPTCP)
            else:
                net.avoid_poor_connections(s.AVOID_POOR_CONNECTIONS_TCP)
        elif name.startswith('rmnet'):
            net.rmnet(name[5])
        else:
            my_print_err('unknown: SKIP')
            continue

        my_print("Connecting: Wait 5 seconds")
        time.sleep(5)

        # Network of the router
        if tc:
            # Losses
            netem = net.loss_cmd(net.get_value_between(tc, 'L', 'p'))
            # Delay
            netem += net.delay_cmd(net.get_value_between(tc, 'D', 'm'))
            if netem:
                net.enable_netem(netem)

        # On reboot, set mutipath_control
        if tcp_mode is TCP.MPTCP:
            net.multipath_control()
        elif tcp_mode is TCP.MPTCP_FULLMESH:
            net.multipath_control_fullmesh(backup=False)
        elif tcp_mode is TCP.MPTCP_FULLMESH_RR:
            net.multipath_control_fullmesh(backup=False, rr=True)
        elif tcp_mode is TCP.MPTCP_BACKUP:
            net.multipath_control_fullmesh(backup=True)
        elif tcp_mode is TCP.MPTCP_NDIFFPORTS:
            net.multipath_control_ndiffports()
        else:
            net.multipath_control(action="disable")

        # Launch test (with net_mode.name to have the full name)
        dev.launch_all(uitests_dir, net_mode.name, tcp_mode, output_dir, s.LAUNCH_FUNC_INIT, s.LAUNCH_FUNC_START, s.LAUNCH_FUNC_END, s.LAUNCH_FUNC_EXIT, s.LAUNCH_UITESTS_ARGS)

        # Delete Netem
        if tc:
            net.disable_netem()

my_print("================ DONE =================\n")

##################################################
##                ROUTER: CLEAN                 ##
##################################################

if s.LIMIT_BW_WSHAPER_SUPPORTED and s.LIMIT_BW:
    net.unlimit_bw_wshaper() # we need to upload traces, no need to keep limitation


##################################################
##                DEVICE: CLEAN                 ##
##################################################

if s.PURGE_TRACES_SMARTPHONE:
    my_print("Remove traces located on the phone")
    dev.adb_shell("rm -r " + s.ANDROID_TRACE_OUT + "*")

    my_print("Remove Facebook pictures")
    dev.adb_shell("rm -rf " + s.ANDROID_HOME + "/Pictures/Facebook/")
    my_print("Remove Drive cache")
    dev.adb_shell("rm -rf " + s.ANDROID_HOME + "/Android/data/com.google.android.apps.docs/files/pinned_docs_files_do_not_edit")


my_print("Reboot the phone") # to avoid possible Android bugs
dev.adb_reboot(wait=False)


##################################################
##                MACHINE: CLEAN                ##
##################################################

# backup traces
if s.BACKUP_TRACES:
    my_print("Backup traces") # better to backup files
    cmd = "bash backup_traces.sh " + arg_dir_exp
    if subprocess.call(cmd.split()) != 0:
        my_print_err(" when using backup_traces.sh with " + arg_dir_exp)
    elif s.START_ANALYSE and not os.path.exists('analyse.skip'):
        my_print("Remotely launch analyze script")
        cmd = ["bash", "start_analyse_distant.sh", os.path.basename(arg_dir_exp) + "/" + now_dir]
        if subprocess.call(cmd) != 0:
            my_print_err(" when using start_analyse.sh with " + cmd[2])


if s.KEEP_TRACES_NB:
    dirs = sorted(os.listdir(arg_dir_exp), reverse=True)
    for rm_dir in dirs[s.KEEP_TRACES_NB:]:
        my_print("Remove previous traces: " + rm_dir)
        shutil.rmtree(os.path.join(arg_dir_exp, rm_dir))
