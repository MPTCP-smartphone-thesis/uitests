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

import os
import sys

##################################################
##                    CONFIG                    ##
##################################################

# switch to True to always rebuild the jar
DEVEL = False
# switch to False to not purge files on the smartphone
PURGE_TRACES_SMARTPHONE = True
# Remove old traces at the end and keep the X last one (False or 0 to not remove traces)
KEEP_TRACES_NB = False
# Reboot the phone before each batch of uitests and at the end of the script
ADB_REBOOT = True
# Backup your traces by launching backup_traces.sh script
BACKUP_TRACES = True
# Capture traces on the proxy (by using *_full_pcap_distant.sh scripts)
CAPTURE_ON_PROXY = True

# If we can control WiFi router: don't forget to check ssh connexion is OK
CTRL_WIFI = True
# Ip of the router
IP_ROUTER = "192.168.1.1"
# IFaces to modify on the router
IFACE_ROUTER = ['wlan0','wlan1']
# User and password
USER_ROUTER = "root"
PASSWORD_ROUTER = "root"

# Tests with TCP (without MPTCP)
WITH_TCP = True
# Tests with (and without) MPTCP support
WITH_MPTCP = True
# MPTCP with FULLMESH
WITH_FULLMESH = False

# If SSH tunnel is installed
SSH_TUNNEL_INSTALLED = True
# Using SSH tunnel (proxy socks via SSH)
WITH_SSH_TUNNEL = True
# Local port used by Redsocks with SSH Tunnel (see SSHTunnel settings)
SSHTUNNEL_PORT = 1984
# If ShadowSocks is installed
SHADOWSOCKS_INSTALLED = True
# Using ShadowSocks proxy (cannot use both!)
WITH_SHADOWSOCKS = False
# Local port used by Redsocks with ShadowSocks (see ShadowSocks settings)
SHADOWSOCKS_PORT = 1080

# Timeout for each test which is launched: 3
TIMEOUT = 60*3
# External host to ping in order to check that everything is ok
EXT_HOST = "google.com"
# Force the use of colours in messages sent to stdout/stderr
FORCE_COLORS = False

# Kind of network tests
# rmnet: 4G/3G/2G
# both[234]: wlan + rmnet[234]
# With TC:
#      - L5p: Losses of 5%
#      - D10m: Delay of 10ms
NETWORK_TESTS = 'wlan both4 both3 rmnet4 rmnet3 both4TCL5p both4TCL15p both4TCD10m both4TCD100m both4TCD1000m both4TCL5pD100m'
# Enable Android's Wi-Fi option: Avoid Poor Connections (Don't use a Wi-Fi network unless it has a good Internet connection)
AVOID_POOR_CONNECTIONS = False
# Functions that can be launched just before/after each uitest
LAUNCH_FUNC_START = False
LAUNCH_FUNC_END = False
# Extras args that could be added to each uitests (not the exceptions)
LAUNCH_UITESTS_ARGS = False

# Possible to restrict to these uitests (name of the directory, e.g. uitests-drive)
RESTRICT_UITESTS = []
# Possible to limit the number of tests, e.g. 1: only one random uitest will be used
RESTRICT_UITESTS_NB = False
# Exceptions for uitests: which are useful just to prepare tests
UITESTS_EXCEPTIONS = ["uitests-preference_network", "uitests-multipath_control", "uitests-ssh_tunnel", "uitests-kill_app", "uitests-shadow_socks"]
# Black list: do not use these uitests dirs:
UITESTS_BLACKLIST = [""]

# Home dir on Android
ANDROID_HOME = "/storage/sdcard0"
ANDROID_TRACE_OUT = ANDROID_HOME + '/traces'
# The default directory to save traces on host, if not provided by args
OUTPUT_DIR = "~/Thesis/TCPDump"

# force to be in the right dir
root_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(root_dir)

# load external config: can be used to change variables here above
CONFIG_FILE_DEFAULT = 'launch_tests_conf.py'
if len(sys.argv) > 1:
    CONFIG_FILE = sys.argv[1]
else:
    CONFIG_FILE = CONFIG_FILE_DEFAULT
if os.path.isfile(CONFIG_FILE):
    g = globals()
    conf_module = __import__(CONFIG_FILE[:-3])
    all_vars = [name for name in dir(conf_module) if not name.startswith('_')]
    for var in all_vars:
        g[var] = getattr(conf_module, var)


##################################################
##                    COLORS                    ##
##################################################

if FORCE_COLORS or sys.stdout.isatty():
    GREEN     = "\033[1;32m" # + bold
    YELLOW    = "\033[0;33m"
    BLUE      = "\033[0;34m"
    WHITE_STD = "\033[0;39m"
else:
    GREEN = YELLOW = BLUE = WHITE_STD = ''

if FORCE_COLORS or sys.stderr.isatty():
    RED       = "\033[1;31m" # + bold
    WHITE_ERR = "\033[0;39m"
else:
    err = WHITE_ERR = ''



##################################################
##                CONFIG CHECKS                 ##
##################################################

# Cannot have both SSH/Shadow socks proxy
if WITH_SSH_TUNNEL and WITH_SHADOWSOCKS:
    my_print_err("Cannot have both SSHTunnel and ShadowSocks: used ShadowSocks")
    WITH_SSH_TUNNEL = False

if WITH_SSH_TUNNEL and not SSH_TUNNEL_INSTALLED:
    my_print_err("SSHTunnel not installed: switch to ShadowSocks if installed")
    WITH_SSH_TUNNEL = False
    WITH_SHADOWSOCKS = SHADOWSOCKS_INSTALLED

if WITH_SHADOWSOCKS and not SHADOWSOCKS_INSTALLED:
    my_print_err("ShadowSocks not installed: switch to SSHTunnel if installed")
    WITH_SHADOWSOCKS = False
    WITH_SSH_TUNNEL = SSH_TUNNEL_INSTALLED

# We only have time for 2 tests
if WITH_MPTCP and WITH_TCP and WITH_FULLMESH:
    my_print_err("Cannot launch MPTCP/TCP/MPTCP-FM: disable MPTCP")
    WITH_MPTCP = False
