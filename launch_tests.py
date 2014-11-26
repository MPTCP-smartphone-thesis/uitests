#! /usr/bin/python3
# -*- coding: utf-8 -*-
#
#  Copyright 2014 Matthieu Baerts & Quentin De Coninck
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
# ./launch_tests.py [trace_dir]
#
# To install on this machine: ant, adb, android, sshpass
# Don't forget to load your SSH key for save_traces_purge_phone.sh script!

import os
import random
import shutil # rmtree
import subprocess
import sys
import time

from enum import Enum

# switch to True to always rebuild the jar
DEVEL = False
# switch to False to not purge files
PURGE = True
# If we can control WiFi router: don't forget to check ssh connexion is OK
CTRL_WIFI = True
# Ip of the router
IP_ROUTER = "192.168.1.1"
# IFaces to modify on the router
IFACE_ROUTER = ['wlan0','wlan1']
# User and password
USER_ROUTER = "root"
PASSWORD_ROUTER = "root"
# Reboot the phone at the end
REBOOT = True
# Backup your traces by launching backup_traces.sh script
BACKUP_TRACES = True
# Tests with (and without) MPTCP support
WITH_MPTCP = True
# Timeout for each test which is launched: 3
TIMEOUT = 60*3
# External host to ping in order to check that everything is ok
EXT_HOST = "ns328523.ip-37-187-114.eu"

# Exceptions for uitests: which are useful just to prepare tests
UITESTS_EXCEPTIONS = ["uitests-preference_network", "uitests-multipath_control", "uitests-ssh_tunnel", "uitests-kill_app"]
# Home dir on Android
ANDROID_HOME = "/storage/sdcard0"
ANDROID_TRACE_OUT = ANDROID_HOME + '/traces'
ANDROID_TCPDUMP_PID = ANDROID_TRACE_OUT + '/.tcpdump.pid'
# The default directory to save traces on host, if not provided by args
DEFAULT_DIR = "~/Thesis/TCPDump"

##############

if sys.stdout.isatty():
    GREEN     = "\033[1;33m" # + bold
    BLUE      = "\033[0;34m"
    WHITE_STD = "\033[0;39m"
else:
    GREEN = BLUE = WHITE_STD = ''

if sys.stderr.isatty():
    red       = "\033[1;31m" # + bold
    WHITE_ERR = "\033[0;39m"
else:
    err = WHITE_ERR = ''

# custom print
def my_print(msg):
    print(GREEN + "\n[" + time.strftime("%Y%m%d-%H%M%S") + "] " + msg + "\n" + WHITE_STD)

def my_print_err(msg):
    print(red + "\n[" + time.strftime("%Y%m%d-%H%M%S") + "]\t*** ERROR " + msg + "\n" + WHITE_ERR, file=sys.stderr)

##############

my_print("Starting tests " + time.ctime())
now_dir = time.strftime("%Y%m%d-%H%M%S")

# Prepare output dir
if len(sys.argv) > 1:
    arg_dir = sys.argv[1]
else:
    arg_dir = DEFAULT_DIR
arg_dir_exp = os.path.expanduser(arg_dir)
output_dir = os.path.join(arg_dir_exp, now_dir)
if (not os.path.isdir(output_dir)):
    os.makedirs(output_dir)
my_print("Save tcpdump files in " + output_dir)

# force to be in the right dir
root_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(root_dir)

my_print("Git version:")
cmd = "git describe --abbrev=0 --dirty --always"
subprocess.call(cmd.split())
print("\n======================================\n\n")

# should start with uitests, not an exception and with build.xml file
def is_valid_uitest(dir):
    if not dir.startswith('uitests-'):
        return False
    if dir in UITESTS_EXCEPTIONS:
        return False
    return os.path.isfile(os.path.join(dir, 'build.xml'))

# Get list of uitest dir (should contain build.xml file)
uitests_dir = []
for file in os.listdir('.'):
    if is_valid_uitest(file):
        uitests_dir.append(file)

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

################################################################################

def adb_shell(cmd, uiautomator=False, args=False):
    if uiautomator:
        full_cmd = "uiautomator runtest " + ANDROID_HOME + "/uitests-" + uiautomator + ".jar -c " + app + ".LaunchSettings"
        if args:
            full_cmd += " -e "
    else:
        full_cmd = cmd
    adb_cmd = ['adb', 'shell', full_cmd + '; echo $?']
    last_line = '1'

    proc = subprocess.Popen(adb_cmd, stdout=subprocess.PIPE)

    # print each line, keep the last one
    while True:
        line = proc.stdout.readline()
        if line != '':
            last_line = line.rstrip()
            print(BLUE + last_line + WHITE_STD)
        else:
            break

    try:
        rc = int(last_line)
    except ValueError as e:
        my_print_err("when launching this cmd on the device: " + cmd)
        return False
    return rc == 0

def adb_shell_root(cmd):
    su_cmd = 'su sh -c "' + cmd + '"'
    return adb_shell(su_cmd)

# relaunch SSH-Tunnel and check the connection via a ping
def restart_proxy(sleep=0):
    cmd_ping = "ping -c 2 " + EXT_HOST
    adb_shell(cmd_ping) ## to avoid strange DNS problems
    if not adb_shell(False, uiautomator='ssh_tunnel'): return False
    if sleep > 0:
        time.sleep(sleep)
    if adb_shell(cmd_ping): return True ## we could have prob when launching it for the 1st time
    return adb_shell(cmd_ping)

def stop_proxy():
    return adb_shell(False, uiautomator='ssh_tunnel', args='action stop')

# Launch full capture on the server
def manage_capture_server(mode, arg_pcap):
    my_print("Send request to the server to " + mode + " a full capture")
    cmd = "bash " + mode + "_full_pcap_distant.sh " + arg_pcap
    if subprocess.call(cmd.split()) != 0:
        my_print_err("when using " + mode + "_full_pcap_distant.sh with " + arg_pcap)

def manage_capture_device(start, arg_pcap, android_pcap_dir, net):
    if start:
        if net.startswith('wlan'):
            iface = "wlan0"
        elif net.startswith('rmnet'):
            iface = "rmnet0"
        else:
            iface = "wlan0:rmnet0"

        adb_shell_root('mkdir -p ' + android_pcap_dir)

        pcap_file = android_pcap_dir + '/' + arg_pcap + '.pcap'
        return adb_shell_root('tcpdump -i ' + iface + ' -w ' + pcap_file + ' tcp & echo $! > ' + ANDROID_TCPDUMP_PID)
    else:
        success = adb_shell_root('kill `cat ' + ANDROID_TCPDUMP_PID + '`')
        adb_shell_root('rm -f ' + ANDROID_TCPDUMP_PID)
        return success

# Launch/Stop full capture on the server and on the device, then restart/stop proxy
def manage_capture(start, app, android_pcap_dir, net, time_now):
    arg_pcap = app + "_" + net + "_" + time_now

    if start: # first the server, then the device
        manage_capture_server("start", arg_pcap)
        manage_capture_device(True, arg_pcap, android_pcap_dir, net)
        restart_proxy()
    else:
        stop_proxy()
        manage_capture_device(False, arg_pcap, android_pcap_dir, net)
        manage_capture_server("stop", arg_pcap)

# Launch test for one app and pull files after each test (if there is a bug)
def launch(app, net, mptcp_dir, out_dir):
    time_now = str(int(time.time()))
    out_dir_app = os.path.abspath(os.path.join(out_dir, app)) # mptcp/net/app
    android_pcap_dir = ANDROID_TRACE_OUT + '/' + mptcp_dir + '/' + net + '/' + app

    # Start full capture on the proxy and on the device
    manage_capture(True, app, android_pcap_dir, net, time_now)

    my_print("*** Launching tests for [ " + app.upper() + " ] at " + time_now + " for " + net + " ***")
    success = adb_shell(False, uiautomator=app)

    # Kill the app
    app_name_file = os.path.join("uitests-" + app, "app_name.txt")
    try:
        file = open(app_name_file, 'r')
        app_name = file.readline().replace('\n', '')
        file.close()
    except:
        app_name = app.capitalize()
    my_print("Kill app " + app_name)
    adb_shell(False, uiautomator='kill_app', args='app '+app_name)

    # Stop full capture on the proxy and on the device
    manage_capture(False, app, android_pcap_dir, net, time_now)

    # no need to pull useless traces
    if not success:
        cmd = "rm -rf " + ANDROID_TRACE_OUT + '/' + app
        adb_shell(cmd)
        return False

    # Save files: 'traces' external dir already contains the app name
    if not os.path.isdir(out_dir_app):
        os.makedirs(out_dir_app)
    my_print("Pull files to " + out_dir_app)
    cmd = "adb pull " + android_pcap_dir + "/ " + out_dir_app
    if subprocess.call(cmd.split()) != 0:
        my_print_err("when pulling traces for " + app)
    # Files will be saved in ~/Thesis/TCPDump/20141119-195517/MPTCP/NET/youtube/youtube_NET_1456465416.pcap

def launch_all(uitests_dir, net, mptcp_dir, out_base=output_dir):
    # out_dir: ~/Thesis/TCPDump/20141119-195517/MPTCP/NET
    out_dir = os.path.join(out_base, mptcp_dir, net)
    if (not os.path.isdir(out_dir)):
        os.makedirs(out_dir)

    # random: to avoid having the same order
    random.shuffle(uitests_dir)
    my_print("Launch all tests for " + net + " with random list: " + str(uitests_dir))

    for uitest in uitests_dir:
        app = uitest[8:]
        launch(app, net, mptcp_dir, out_dir)

    # Compress files
    my_print("Compressing files")
    for app in os.listdir(out_dir):
        app_dir = os.path.abspath(os.path.join(out_dir, app))
        if not os.path.isdir(app_dir): # we can have pid files
            continue
        for trace in os.listdir(app_dir):
            if (trace.endswith('.pcap')):
                trace_path = os.path.join(app_dir, trace)
                my_print("Compressing " + trace_path + " to " + trace_path + ".gz")
                cmd = 'gzip -9 ' + trace_path # or xz/7z format?
                if subprocess.call(cmd.split()) != 0:
                    my_print_err(" when pulling traces for " + app)

## Net: devices
WIFI = 'wifi'
DATA = 'data'

# net should be: '4', '3' or '2'
def change_pref_net(version):
    arg = "network-status " + version + "G"
    return adb_shell(False, uiautomator='preference_network', args=arg)

# 'wifi', 'enable'
def manage_net(iface, status):
    my_print(status + " " + iface)
    return adb_shell_root('svc ' + iface + ' ' + status)

def enable_iface(iface):
    return manage_net(iface, 'enable')

def disable_iface(iface):
    return manage_net(iface, 'disable')

def prefer_iface(iface):
    return manage_net(iface, 'prefer')

def rmnet(version):
    disable_iface(WIFI)
    enable_iface(DATA)
    change_pref_net(version)

def both(version, prefer_wifi=True):
    enable_iface(WIFI)
    enable_iface(DATA)
    if prefer_wifi:
        prefer_iface(WIFI)
    else:
        prefer_iface(DATA)
    change_pref_net(version)

## Net: router

def get_value_between(s, start, end):
    index = s.find(start)
    if index >= 0:
        return s[index+1:s.index(end, index+1)]
    return False

def loss_cmd(value):
    if value:
        return " loss " + value + "%"
    return ""

def delay_cmd(value):
    if value:
        return " delay " + value + "ms"
    return ""

def router_shell(cmd):
    router_cmd = "sshpass -p " + PASSWORD_ROUTER + " ssh " + USER_ROUTER + "@" + IP_ROUTER + " " + cmd
    if subprocess.call(router_cmd.split()) != 0:
        my_print_err("when launching this cmd on the router: " + cmd)
        return False
    return True

def enable_netem(netem):
    rc = True
    for iface in IFACE_ROUTER:
        cmd = "tc qdisc add dev " + iface + " root netem " + netem
        rc &= router_shell(cmd)
    return rc

def disable_netem():
    rc = True
    for iface in IFACE_ROUTER:
        rc &= router_shell("tc qdisc delete dev " + iface + " root")
    return rc

# 'enable' or 'disable'
def multipath_control(action):
    return adb_shell(False, uiautomator='multipath_control', args='action '+action)

################################################################################


# Check router OK and insert mod + delete rules
if CTRL_WIFI:
    my_print("Checking router connexion")
    if (not router_shell("echo OK")):
        my_print_err("Not able to be connected to the router, exit")
        exit(1)
    my_print("Reset Netem (tc), ignore errors")
    router_shell("insmod /lib/modules/3.3.8/sch_netem.ko")
    disable_netem()

my_print("Remove previous traces located on the phone")
adb_shell("rm -r " + ANDROID_TRACE_OUT + "*")

# rmnet: 4G/3G/2G
# both[234]: wlan + rmnet[234]
# With TC:
#      - L5p: Losses of 5%
#      - D10m: Delay of 10ms
Network = Enum('Network', 'wlan both4 both3 rmnet4 rmnet3 both4Data both4TCL5p both4TCL15p both4TCD10m both4TCD100m both4TCD1000m both4TCL5pD100m')

# With or without mptcp
mptcp = [True, False]
random.shuffle(mptcp)

for with_mptcp in mptcp:
    # Check MPTCP
    if with_mptcp:
        if not WITH_MPTCP:
            my_print("MPTCP not supported, skip")
            continue
        stop_proxy() ## prevent error when enabling mptcp
        multipath_control("enable")
        mptcp_dir = "MPTCP"
    else:
        stop_proxy() ## prevent error when disabling mptcp
        multipath_control("disable")
        mptcp_dir = "TCP"

    my_print("============ Kernel mode: " + mptcp_dir + " =========\n")

    # All kinds of networks
    net_list = list(Network)
    random.shuffle(net_list)
    my_print("Network list:")
    print(*(net.name for net in net_list))

    for net in net_list:
        name = net.name
        my_print("========== Network mode: " + name + " ===========\n")
        tc = False
        index = name.find('TC')
        if index >= 0:
            if not CTRL_WIFI:
                my_print_err('We do not control the WiFi router, skip this test')
                continue
            tc = name[index+2:]
            name = name[0:index]

        stop_proxy() ## prevent error when changing network connections

        # Network of the device
        if net == Network.wlan:
            enable_iface(WIFI)
            disable_iface(DATA)
        elif net == Network.both4Data: # prefer data
            both('4', prefer_wifi=False)
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
        launch_all(uitests_dir, net.name, mptcp_dir)

        # Delete Netem
        if tc:
            disable_netem()

my_print("================ DONE =================\n")

my_print("Remove traces located on the phone")
adb_shell("rm -r " + ANDROID_TRACE_OUT + "*")

my_print("Reboot the phone") # to avoid possible Android bugs
if REBOOT and subprocess.call("adb reboot".split()) != 0:
    my_print_err(" when rebooting the phone")

# backup traces
my_print("Backup traces") # better to backup files
cmd = "bash backup_traces.sh " + arg_dir_exp
if BACKUP_TRACES and subprocess.call(cmd.split()) != 0:
    my_print_err(" when using backup_traces.sh with " + arg_dir_exp)
