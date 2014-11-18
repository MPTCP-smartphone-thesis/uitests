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
import subprocess
import sys
import time

from enum import Enum

# switch to True to always rebuild the jar
DEVEL = False
# switch to False to not purge files
PURGE = True
# If we can control WiFi router
CTRL_WIFI = True
# Home dir on Android
android_home = "/storage/sdcard0"

print("Starting tests " + time.ctime())
now_dir = time.strftime("%Y%m%d-%H%M%S")

# Prepare output dir
if len(sys.argv) > 1:
    arg_dir = sys.argv[1]
else:
    arg_dir = "~/Thesis/TCPDump"
output_dir = os.path.join(os.path.expanduser(arg_dir), now_dir)
if (not os.path.isdir(output_dir)):
    os.makedirs(output_dir)
print("Save tcpdump files in " + output_dir)

# force to be in the right dir
root_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(root_dir)

print("Git version:")
cmd = "git describe --abbrev=0 --dirty --always"
subprocess.call(cmd.split())

# Get list of uitest dir (should contain build.xml file)
uitests_dir = []
for file in os.listdir('.'):
    if file.startswith('uitests-') and not file == "uitests-preference_network" and os.path.isfile(os.path.join(file, 'build.xml')):
        uitests_dir.append(file)

# Prepare the tests (build the jar if needed)
for uitest in uitests_dir + ["uitests-preference_network"]:
    app = uitest[8:]
    print("Checking requirements for " + app)
    # Create project if needed
    if DEVEL or not os.path.isfile(os.path.join(uitest, 'local.properties')):
        print("Creating uitest-project")
        cmd = "android create uitest-project -n " + uitest + " -t 1 -p " + uitest
        if subprocess.call(cmd.split()) != 0:
            print("ERROR when creating uitest-project for " + app, file=sys.stderr)
            continue

    # Build project and push jar if needed
    jar_file = os.path.join(uitest, 'bin', uitest + '.jar')
    if DEVEL or not os.path.isfile(jar_file):
        print("Build ant and push jar")
        os.chdir(uitest)
        cmd = "ant build"
        rt = subprocess.call(cmd.split())
        os.chdir(root_dir)
        if rt != 0:
            print("ERROR when building jar for " + app, file=sys.stderr)
            continue
        # push the new jar
        cmd = "adb push " + jar_file + " " + android_home + "/" + uitest + ".jar"
        if subprocess.call(cmd.split()) != 0:
            print("ERROR when pushing jar for " + app, file=sys.stderr)
            continue


################################################################################

def adb_shell(cmd):
    adb_cmd = "adb shell " + cmd
    if subprocess.call(adb_cmd.split()) != 0:
        print("ERROR when launching this cmd on the devise: " + cmd, file=sys.stderr)
        return False
    return True

def adb_shell_root(cmd):
    su_cmd = 'su sh -c "' + cmd + '"'
    return adb_shell(su_cmd)

# Launch test for one app and pull files
def launch(app, net, out_base = output_dir):
    print("Launching tests for " + app + " at " + str(int(time.time())) + " for " + net)
    cmd = "uiautomator runtest " + android_home + "/uitests-" + app + " -c " + app + ".LaunchSettings"
    if not adb_shell(cmd): return

    # Save files: 'traces' external dir already contains the app name
    print("Pull files")
    out_dir = os.path.join(out_base, net)
    os.makedirs(out_dir)
    cmd = "adb pull " + android_home + "/traces/ " + os.path.abspath(out_dir)
    if subprocess.call(cmd.split()) != 0:
        print("ERROR when pulling traces for " + app, file=sys.stderr)

    # Move previous traces on the device
    cmd = "mv " + android_home + "/traces/* " + android_home + "/traces_" + net
    if not adb_shell(cmd): return

def launch_all(uitests_dir, net):
    cmd = "mkdir -p " + android_home + "/traces_" + net
    if not adb_shell(cmd): return

    # random: to avoid having the same order
    random.shuffle(uitests_dir)
    print("Launch all tests for " + net + " with random list: " + str(uitests_dir))

    for uitest in uitests_dir:
        app = uitest[8:]
        launch(app)

## Net: devise
WIFI = 'wifi'
DATA = 'data'

# net should be: '4', '3' or '2'
def change_pref_net(version):
    cmd = "uiautomator runtest " + android_home + "/uitests-" + app + " -c " + app + ".LaunchSettings -e network-status " + version + "G"
    return adb_shell(cmd)

# 'wifi', 'enable'
def manage_net(iface, status):
    print(status + " " + iface)
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

################################################################################


# rmnet: 4G/3G/2G
# both[234]: wlan + rmnet[234]
# With TC:
#      - L5p: Losses of 5%
#      - D10m: Delay of 10ms
Network = Enum('Network', 'wlan both4 both3 both2 rmnet4 rmnet3 rmnet2 both4TCData both4TCL5p both4TCL15p both4TCD10m both4TCD100m both4TCD1000m both4TCL5pD100m')

# All kinds of networks
net_list = list(Network)
random.shuffle(net_list)

# Check router OK and insert mod + delete rules
if CTRL_WIFI:
    if (not router_shell("echo OK"))
        return 1
    router_shell("insmod /lib/modules/3.3.8/sch_netem.ko")
    router_shell("tc qdisc delete dev " + IFACE_ROUTER + " root")

for net in net_list:
    name = net.name
    print('Network mode: ' + name)
    index = name.find('TC')
    if index >= 0:
        if not CTRL_WIFI:
            print('We do not control the WiFi router, skip this test')
            continue
        tc = name[index+2:]
        name = name[0:index]
    else:
        tc = False

    # Network of the devise
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
        print('unknown: SKIP')
        continue

    launch_all(uitests_dir, net.name)

# Save the traces and purge the phone
cmd = "bash save_traces_purge_phone.sh " + arg_dir
if subprocess.call(cmd.split()) != 0:
    print("ERROR when using save_traces_purge_phone with " + arg_dir, file=sys.stderr)
