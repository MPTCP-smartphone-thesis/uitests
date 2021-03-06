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
# Backup your traces by launching backup_traces.sh script at the end of the script
BACKUP_TRACES = True
# Launch start_analyse_distant.sh script at the end of the script
START_ANALYSE = True
# Capture traces on the proxy (by using *_full_pcap_distant.sh scripts)
CAPTURE_ON_PROXY = True
# Sleep 5 minutes before launching compression on the server
COMPRESS_SLEEP = 5*60

# If we can control WiFi router: don't forget to check ssh connexion is OK
CTRL_WIFI = True
# IP of the routers
IP_ROUTER = ["192.168.1.1"]
# IFaces to modify on the router
IFACE_ROUTER = ['wlan0', 'eth0.2'] # or ['wlan0','eth1']
# Devices to modify on the router
DEVICES_ROUTER = ['phy0'] # ['phy0','phy1']
# User and password
USER_ROUTER = "root"
PASSWORD_ROUTER = "root" # or None/False to use key and sshpass will no longer be needed
# Default External IP (will be overwritten in launch_tests.py except problem)
EXTERNAL_IP = "127.0.0.1"

# Tests with TCP (without MPTCP)
WITH_TCP = True
# Tests with (and without) MPTCP with the 'default' PM (do not create subflows)
WITH_MPTCP = False
# MPTCP with FULLMESH
WITH_MPTCP_FULLMESH = True
# MPTCP with FULLMESH and round robin as schedulers
WITH_MPTCP_FULLMESH_ROUND_ROBIN = False
# MPTCP with backup mode (for data), iproute with multipath support is needed
WITH_MPTCP_BACKUP = False
# MPTCP with 'ndiffports' path manager: X subflows will be created across the same pair of IP-addresses, modifying the source-port
WITH_MPTCP_NDIFFPORTS = False
# Number of subflows per IP-addresses
NDIFFPORTS_DEFAULT_NB = 2
# iproute needs to support multipath: https://github.com/MPTCP-smartphone-thesis/android-iproute2
IPROUTE_WITH_MULTIPATH = False
# Default route via WLan or RMNet?
IPROUTE_DEFAULT_ROUTE_WLAN = True

# Default list of allowed TCP congestion control algorithms (set to false to not override the default list)
# Full list: "cubic reno bic westwood highspeed hybla htcp vegas veno scalable lp yeah illinois lia olia wvegas"
TCP_CONGESTION_CONTROL_ALLOWED_DEFAULT = "cubic reno"
# Default TCP congestion control algorithms
TCP_CONGESTION_CONTROL_DEFAULT = "cubic"
# With weighted Vegas (wvegas) instead of the default one
WITH_TCP_CONGESTION_CONTROL_WVEGAS = False


# If SSH tunnel is installed
SSH_TUNNEL_INSTALLED = False
# Using SSH tunnel (proxy socks via SSH)
WITH_SSH_TUNNEL = False
# Local port used by Redsocks with SSH Tunnel (see SSHTunnel settings)
SSHTUNNEL_PORT = 1984
# If ShadowSocks is installed
SHADOWSOCKS_INSTALLED = True
# Using ShadowSocks proxy (cannot use both!)
WITH_SHADOWSOCKS = True
# Local port used by Redsocks with ShadowSocks (see ShadowSocks settings)
SHADOWSOCKS_PORT = 1080
# Capture on 'any' ifaces (all except lo with 127.0.0.1 filter)
CAPTURE_ON_ANY = True # useful to get ack retransmit, etc.
# Capture on 'lo' iface (with filters)
CAPTURE_ON_LO = True  # useful to get real server addresses
# IP/port Proxy: when capturing on 'any', only catch TCP packages from/to this IP and/or port
PROXY_IP = False
PROXY_PORT = False
# Mean value for a RTT to the proxy (in ms)
PROXY_RTT = 7

# Timeout for each test which is launched: 3
TIMEOUT = 60*3
# Number of time a test will be relaunched if it fails (0 means no retry)
LAUNCH_RETRY_MAX = 0
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
NETWORK_TESTS = 'wlan both4 both3 rmnet4 rmnet3 both4TCL1p both4TCL5p both4TCD5m both4TCD50m'
# Enable Android's Wi-Fi option: Avoid Poor Connections (Don't use a Wi-Fi network unless it has a good Internet connection)
AVOID_POOR_CONNECTIONS_TCP = False
AVOID_POOR_CONNECTIONS_MPTCP = False
# Limit Bandwidth: (up, down) or [(up, down), (up, dow)] in kpbs ; e.g.:
#   1Mbps↓, 15Mbps↑: (1000, 15000)
#   1Mbps↓, 15Mbps↑ for router 1 (see IP_ROUTER) and 100kbps↓, 1.5Mbps↑ for router 2: [(1000, 15000), (100, 1500)]
LIMIT_BW = False
# Shaper mode, select the first one which is true
LIMIT_BW_WITH_SHAPER  = True  # our script which also support losses/delays
LIMIT_BW_WITH_WSHAPER = False # losses/delays at the same time not supported!
LIMIT_BW_WITH_RATE    = False # just use 'rate' without other rules
WAN_IFACE = 'eth0.2' # UPLINK
LAN_IFACE = 'wlan0'  # DOWNLING
# Functions that can be launched just before/after each uitest
LAUNCH_FUNC_INIT  = False # before start, in the current thread
LAUNCH_FUNC_START = False # in a new thread, just before launching the uitests
LAUNCH_FUNC_END   = False # just after the uitest, in the current thread
LAUNCH_FUNC_EXIT  = False # just after having stopped captures
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

GREEN     = "\033[1;32m" # + bold
YELLOW    = "\033[0;33m"
BLUE      = "\033[0;34m"
WHITE_STD = "\033[0;39m"
RED       = "\033[1;31m" # + bold
WHITE_ERR = "\033[0;39m"

# load external config: can be used to change variables here above
CONFIG_FILE_DEFAULT = 'launch_tests_conf.py'



##################################################
##                     INIT                     ##
##################################################

def init():
    global CONFIG_FILE, CONFIG_FILE_DEFAULT
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

    # COLOURS
    global FORCE_COLORS
    if not FORCE_COLORS:
        if not sys.stdout.isatty():
            global GREEN, YELLOW, BLUE, WHITE_STD
            GREEN = YELLOW = BLUE = WHITE_STD = ''
        if not sys.stderr.isatty():
            global RED, WHITE_ERR
            RED = WHITE_ERR = ''

    # Cannot have both SSH/Shadow socks proxy
    global WITH_SSH_TUNNEL, WITH_SHADOWSOCKS, SSH_TUNNEL_INSTALLED, SHADOWSOCKS_INSTALLED
    if WITH_SSH_TUNNEL and WITH_SHADOWSOCKS:
        print("Cannot have both SSHTunnel and ShadowSocks: used ShadowSocks", file=sys.stderr)
        WITH_SSH_TUNNEL = False

    if WITH_SSH_TUNNEL and not SSH_TUNNEL_INSTALLED:
        print("SSHTunnel not installed: switch to ShadowSocks if installed", file=sys.stderr)
        WITH_SSH_TUNNEL = False
        WITH_SHADOWSOCKS = SHADOWSOCKS_INSTALLED

    if WITH_SHADOWSOCKS and not SHADOWSOCKS_INSTALLED:
        print("ShadowSocks not installed: switch to SSHTunnel if installed", file=sys.stderr)
        WITH_SHADOWSOCKS = False
        WITH_SSH_TUNNEL = SSH_TUNNEL_INSTALLED

    # Cannot use Backup if IPRoute doesn't support multipath option
    global WITH_MPTCP_BACKUP, IPROUTE_WITH_MULTIPATH
    if WITH_MPTCP_BACKUP and not IPROUTE_WITH_MULTIPATH:
        print("Iproute not supporting multipath but using Backup mode: disable MPTCP with backup", file=sys.stderr)
        WITH_MPTCP_BACKUP = False

    # LIMIT BW only if LIMIT_BW_WITH_*
    global LIMIT_BW_WITH_SHAPER, LIMIT_BW_WITH_WSHAPER, LIMIT_BW_WITH_RATE, LIMIT_BW, CTRL_WIFI, NETWORK_TESTS
    if LIMIT_BW:
        if not CTRL_WIFI:
            print("Not controlling WiFi router: not able to limit bandwidth", file=sys.stderr)
            sys.exit(1)
        elif LIMIT_BW_WITH_WSHAPER and NETWORK_TESTS.find('TC') >= 0:
            print("WShaper doesn't support delays/losses", file=sys.stderr)
            sys.exit(1)
        elif not LIMIT_BW_WITH_SHAPER and not LIMIT_BW_WITH_WSHAPER and not LIMIT_BW_WITH_RATE:
            print("No shaper detected, disable shaping", file=sys.stderr)
            LIMIT_BW = False

def print_vars(file=sys.stdout):
    g = globals().copy()
    for var in g:
        if not var.startswith('_') and var.isupper():
            print(var + ' = ' + str(g[var]), file=file)
