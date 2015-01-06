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
# ./launch_tests.py [CONFIG_FILE.py]
#
# To install on this machine: ant, adb, android, sshpass
# Don't forget to load your SSH key for backup_traces.sh script!

import os
import random
import shutil # rmtree
import subprocess
import sys
import threading
import time

from enum import Enum

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

# custom print
def my_print(msg, start=GREEN):
    print(start + "\n[" + time.strftime("%Y%m%d-%H%M%S") + "] " + msg + "\n" + WHITE_STD)

def my_print_err(msg, start=RED):
    print(start + "\n[" + time.strftime("%Y%m%d-%H%M%S") + "]\t*** ERROR " + msg + "\n" + WHITE_ERR, file=sys.stderr)


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


##################################################
##            PREPARE TESTS: MACHINE            ##
##################################################

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
##                DEVICE: METHODS               ##
##################################################

def adb_restart():
    try:
        ps_out = subprocess.check_output("ps -xwwo user,pid,cmd".split(), universal_newlines=True).splitlines()
        for line in ps_out:
            ps = line.split(maxsplit=2)
            if ps[2].startswith("adb ") and "fork-server" in ps[2]:
                if ps[0] != os.getenv('USER'):
                    my_print_err("adb owned by another user: not restarting it")
                    return False
                break
    except:
        my_print_err("Not able to launch ps command")
        my_print("adb: restart server")
        if subprocess.call("adb kill-server".split()) != 0: return False
        if subprocess.call("adb start-server".split()) != 0: return False
        return True

# kill_adb_restart_usb_listener.sh need to be launched as root
def adb_restart_root():
    file = open('.adb_reboot', 'a')
    file.write(time.ctime() + '\n')
    file.close()
    time.sleep(15)
    return subprocess.call("adb start-server".split()) != 0

def adb_shell_timeout(proc):
    try:
        proc.wait(TIMEOUT)
    except:
        my_print_err("(timeout) when launching this cmd on the device: " + str(proc.args))
        proc.terminate()

def adb_shell(cmd, uiautomator=False, args=False, out=False, restart=0):
    if uiautomator:
        full_cmd = "uiautomator runtest " + ANDROID_HOME + "/uitests-" + uiautomator + ".jar -c " + uiautomator + ".LaunchSettings"
        if args:
            if type(args) == list:
                for arg in args:
                    full_cmd += " -e " + arg
            else:
                full_cmd += " -e " + args
    else:
        full_cmd = cmd
    adb_cmd = ['adb', 'shell', full_cmd + '; echo $?']
    last_number = 0
    error = dev_not_found = False
    if out:
        result = []
    else:
        result = True

    # adb shell doesn't return the last exit code...
    proc = subprocess.Popen(adb_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    thread = threading.Thread(target=adb_shell_timeout, args=(proc,))
    thread.start()

    line = line_err = True
    # print each line, keep the last one
    while proc.poll() == None or line or line_err:
        line_err = proc.stderr.readline()
        if line_err:
            line_err_strip = line_err.rstrip()
            if line_err_strip == 'error: device not found':
                dev_not_found = True
            print(RED + line_err_strip + WHITE_ERR, file=sys.stderr)

        line = proc.stdout.readline()
        if line:
            last_line = line.rstrip()
            if uiautomator and last_line.lower().startswith('failure'):
                error = True
                print(RED + last_line + WHITE_ERR, file=sys.stderr)
            elif out:
                result.append(last_line)
            else:
                print(BLUE + last_line + WHITE_STD)
            if len(last_line) < 4:
                try:
                    number = int(last_line)
                    if number >= 0 or number <= 255:
                        last_number = number
                except ValueError as e:
                    pass

    if dev_not_found:
        if restart == 0:
            my_print_err("Device not found, restart adb server and retry: " + full_cmd)
            adb_restart()
        elif restart == 1:
            my_print_err("Device not found, restart adb server (root) and retry: " + full_cmd)
            adb_restart_root() # try root if problem
        elif restart > 1 and restart < 6: # max 2h
            my_print_err("Device not found, sleep 30 minutes (" + str(restart-1) + "), restart adb server (root) and retry: " + full_cmd)
            time.sleep(1800)
            adb_restart_root()
        else:
            my_print_err("Device not found, skip this command: " + full_cmd)
            return False
        return adb_shell(cmd, uiautomator, args, out, restart+1)

    rc = proc.returncode
    if rc != 0 or error:
        my_print_err("when launching this cmd on the device: " + full_cmd + " - rc: " + str(rc))
        return False

    if last_number != 0:
        my_print_err("when launching this cmd on the device: " + full_cmd + " - last number: " + last_line)
        return False
    return result

def adb_shell_root(cmd):
    su_cmd = 'su sh -c "' + cmd + '"'
    return adb_shell(su_cmd)

# filename: name of the file or cmd + '.txt'
def adb_shell_write_output(cmd, out_dir, filename=False):
    my_print("Get " + cmd + " from smartphone")
    out = adb_shell(cmd, out=True)
    if out:
        out = '\n'.join(out) # one file
    with open(os.path.join(out_dir, filename if filename else cmd.replace(' ', '_') + '.txt'), "w") as out_file:
        print(out, file=out_file)

def adb_get_uptime():
    up_out = adb_shell("uptime", out=True)
    try:
        return time.strptime(up_out[0][9:17], "%H:%M:%S")
    except:
        my_print_err("Not able to get the uptime")
        return False

LAST_UPTIME = ()
# return True if has rebooted or error
def adb_check_reboot():
    uptime = adb_get_uptime()
    if not uptime: return True

    global LAST_UPTIME
    old_up = LAST_UPTIME
    LAST_UPTIME = uptime

    return old_up > uptime # True if old == ()

# return True if it has rebooted
def adb_check_reboot_sim():
    my_print("Check if we have 'SIM card added' warning")
    rebooted = False
    # SIM warning
    while adb_shell(False, uiautomator='kill_app', args='sim true', out=True): # out to hide error
        my_print("Wait: the smartphone is rebooting")
        time.sleep(60)
        rebooted = True

    up = adb_check_reboot()
    if LAST_UPTIME and LAST_UPTIME < time.strptime("45", "%S"):
        my_print("Uptime is lower than 45 sec, wait 30 seconds more")
        time.sleep(30)
    return rebooted or up or not LAST_UPTIME

def adb_reboot(wait=True):
    if not ADB_REBOOT:
        return True

    success = True
    # Try to reboot it, max 3 times
    for i in range(3):
        success = subprocess.call("adb reboot".split()) == 0
        if success:
            break
        my_print_err("when rebooting the phone... Retry " + str(i))
        # device not found... restart ADB, maybe it can help
        adb_restart()

    # Even after 3 times, we were not able to reboot. Try with an external script
    if wait and not success:
        timeout = False
        for i in range(5): # limit waiting time
            if i > 0 and not timeout:
                time.sleep(30*60)
            adb_restart_root()
            try:
                timeout = False
                success = subprocess.call("adb reboot".split(), timeout=1800) == 0
                if success:
                    break
            except:
                timeout = True
                my_print_err("Device not found... Retry " + str(i))
        if not success:
            my_print_err("Device not found... EXIT")
            sys.exit(1)

    if wait:
        my_print("The device has rebooted, wait 60 sec")
        time.sleep(60)
        if not adb_restart(): # restart: avoid permission problems
            adb_restart_root() # try root if problem

        # check sim card warning
        adb_check_reboot_sim()
        timeout = False
        for i in range(5): # limit waiting time
            if i > 0 and not timeout:
                time.sleep(30*60)
            try:
                timeout = False
                if subprocess.call("adb wait-for-device".split(), timeout=1800) == 0:
                    return True
            except:
                timeout = False
                my_print_err("Device not found... wait and retry " + str(i))
                if not adb_restart(): # restart: avoid permission problems
                    adb_restart_root() # try root if problem
        my_print_err("Device not found... EXIT")
        sys.exit(1)
    return True

# strict: the process name == proc_name
def adb_get_pid(proc_name, strict=False):
    ps_out = adb_shell('ps | grep ' + proc_name, out=True)
    if ps_out:
        output = []
        for line in ps_out:
            if strict and line.endswith(proc_name) or not strict and proc_name in line:
                output.append(line.split()[1])
        return output
    return []

# relaunch SSH-Tunnel and check the connection via a ping
def restart_proxy(sleep=1):
    if not WITH_SSH_TUNNEL:
        return True

    my_print("Restart proxy: ping")
    if EXT_HOST:
        cmd_ping = "ping -c 4 " + EXT_HOST
        adb_shell(cmd_ping) ## to avoid strange DNS problems

    my_print("Restart proxy: ssh tunnel")
    if not adb_shell(False, uiautomator='ssh_tunnel'): return False

    if EXT_HOST:
        time.sleep(sleep)
        my_print("Restart proxy: reping")
        if adb_shell(cmd_ping): return True ## we could have prob when launching it for the 1st time
        return adb_shell(cmd_ping)
    elif sleep > 2: # min 2 sec if we don't use ping
        time.sleep(sleep)
    else:
        time.sleep(2)
    return True

def stop_proxy():
    if not WITH_SSH_TUNNEL:
        return True

    my_print("Stop proxy")
    return adb_shell(False, uiautomator='ssh_tunnel', args='action stop')

# Launch full capture on the server
def manage_capture_server(mode, arg_pcap):
    if not CAPTURE_ON_PROXY:
        return
    my_print("Send request to the server to " + mode + " a full capture")
    cmd = ["bash", mode + "_full_pcap_distant.sh", arg_pcap]
    if subprocess.call(cmd) != 0:
        my_print_err("when using " + mode + "_full_pcap_distant.sh with " + arg_pcap)

def stop_capture_device():
    my_print("Stop capturing traces on the device")
    pids = adb_get_pid('tcpdump')
    out_status = True
    for pid in pids:
        out_status &= adb_shell_root('kill ' + pid)
    if out_status:
        return True
    my_print_err("Not able to kill tcpdump")
    return False

# it seems tcpdump is not launched each time and no error is produced
def launch_capture_device(cmd, instances):
    adb_shell_root(cmd)
    time.sleep(1)
    pids = adb_get_pid('tcpdump')
    i = 0
    while not pids or len(pids) < instances:
        if (i > 19):
            return False
        i += 1
        adb_shell_root(cmd)
        time.sleep(1)
        pids = adb_get_pid('tcpdump')
    return True

def start_capture_device(arg_pcap, android_pcap_dir, net):
    my_print("Capture traces on the device")
    tcp_filter = 'tcp'
    if net.startswith('wlan'):
        iface = "wlan0"
    elif net.startswith('rmnet'):
        iface = "rmnet0"
    else: # both
        iface = "any"
        tcp_filter += ' and not ip host 127.0.0.1'

    adb_shell('mkdir -p ' + android_pcap_dir)
    time.sleep(0.5)

    pcap_file = android_pcap_dir + '/' + arg_pcap + '_' + iface + '.pcap'
    cmd = 'tcpdump -i ' + iface + ' -w ' + pcap_file + ' ' + tcp_filter + ' &'

    if not launch_capture_device(cmd, 1):
        my_print_err("Not able to start tcpdump!")
        return False

    if not WITH_SSH_TUNNEL and not WITH_SHADOWSOCKS:
        return True

    pcap_file_lo = android_pcap_dir + '/' + arg_pcap + '_lo.pcap'
    port_no = SSHTUNNEL_PORT if WITH_SSH_TUNNEL else SHADOWSOCKS_PORT
    cmd_lo = 'tcpdump -i lo -w ' + pcap_file_lo + ' tcp and not port ' + str(port_no) + ' &'
    if not launch_capture_device(cmd_lo, 2):
        my_print_err("Not able to start tcpdump for LoopBack only!")
        stop_capture_device()
        return False
    return True

# Launch/Stop full capture on the server and on the device, then restart/stop proxy
def manage_capture(start, mptcp_dir, app, android_pcap_dir, net, time_now, rm=False):
    arg_pcap = mptcp_dir.lower() + "_" + app + "_" + net + "_" + time_now

    if start: # first the server, then the device
        manage_capture_server("start_sshtunnel" if WITH_SSH_TUNNEL else "start_shadowsocks", arg_pcap)
        if not start_capture_device(arg_pcap, android_pcap_dir, net):
            manage_capture_server("stop", arg_pcap)
            manage_capture_server("rm", arg_pcap)
            return False
        if not restart_proxy():
            stop_capture_device()
            adb_shell('rm -rf ' + android_pcap_dir)
            manage_capture_server("stop", arg_pcap)
            manage_capture_server("rm", arg_pcap)
            return False
        return True
    else:
        success = stop_proxy()
        stop_capture_device()
        manage_capture_server("stop", arg_pcap)
        if rm:
            manage_capture_server("rm", arg_pcap)
        return success

# Launch test for one app and pull files after each test (if there is a bug)
def launch(app, net, mptcp_dir, out_dir):
    time_now = time.strftime("%Y%m%d-%H%M%S")
    out_dir_app = os.path.abspath(os.path.join(out_dir, app)) # mptcp/net/app
    android_pcap_dir = ANDROID_TRACE_OUT + '/' + mptcp_dir + '/' + net + '/' + app

    # Start full capture on the proxy and on the device
    if not manage_capture(True, mptcp_dir, app, android_pcap_dir, net, time_now):
        my_print_err("Error proxy: Skip test of " + app.upper())
        return

    adb_shell_write_output('netstat', out_dir_app, filename='netstat_before.txt')

    my_print("*** Launching tests for [ " + YELLOW + app.upper() + GREEN + " ] at " + time_now + " for " + net + " ***")
    success = adb_shell(False, uiautomator=app)

    adb_shell_write_output('netstat', out_dir_app, filename='netstat_after.txt')

    # Kill the app
    pkg_name_file = os.path.join("uitests-" + app, "pkg_name.txt")
    try:
        file = open(pkg_name_file, 'r')
        pkg_name = file.readlines()[0].replace('\n', '')
        file.close()
        my_print("Force stop app " + app + " - " + pkg_name)
        adb_shell_root("am force-stop " + pkg_name) # root should not be needed
    except:
        my_print_err("Not able to find pkg name and then kill " + app)

    # Stop full capture on the proxy and on the device
    manage_capture(False, mptcp_dir, app, android_pcap_dir, net, time_now, not success)

    # no need to pull useless traces
    if not success:
        my_print("Error during the test, remove traces")
        cmd = "rm -rf " + android_pcap_dir
        adb_shell(cmd)
        return False

    # Save files: 'traces' external dir already contains the app name
    if not os.path.isdir(out_dir_app):
        os.makedirs(out_dir_app)
    my_print("Pull files to " + out_dir_app)
    cmd = "adb pull " + android_pcap_dir + "/ " + out_dir_app
    if subprocess.call(cmd.split()) != 0:
        my_print_err("when pulling traces for " + app)
    # Files will be saved in ~/Thesis/TCPDump/DATE-HOUR-SHA1/MPTCP/NET/APP/MPTCP_APP_NET_DATE_HOUR.pcap + MPTCP_APP_NET_DATE_HOUR_lo.pcap

def launch_all(uitests_dir, net, mptcp_dir, out_base=output_dir):
    # out_dir: ~/Thesis/TCPDump/DATE-HOUR-SHA1/MPTCP/NET
    out_dir = os.path.join(out_base, mptcp_dir, net)
    if (not os.path.isdir(out_dir)):
        os.makedirs(out_dir)

    # Generate seed
    my_print("Generate seed")
    subprocess.call(['./generate_push_random_seed.sh'])

    # random: to avoid having the same order
    random.shuffle(uitests_dir)
    my_print("Launch all tests for " + net + " with random list: " + str(uitests_dir))

    adb_shell_write_output('netcfg', out_dir)
    adb_shell_write_output('netstat', out_dir)

    for uitest in uitests_dir:
        app = uitest[8:]
        time_before = time.time()
        launch(app, net, mptcp_dir, out_dir)
        global TEST_NO
        my_print('UITest ' + str(TEST_NO) + '/' + str(NB_TESTS) + ' for ' + app + ' took ' + str(round(time.time() - time_before)) + ' seconds')
        TEST_NO += 1

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


##################################################
##            DEVICE/ROUTER: NETWORK            ##
##################################################

## Net: devices
WIFI = 'wifi'
DATA = 'data'

# net should be: '4', '3' or '2'
def change_pref_net(version):
    my_print("Settings: prefer " + version + "G")
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

# 'enable' or 'disable'
def multipath_control(action, path_mgr=False):
    stop_proxy() ## prevent error when enabling mptcp
    my_print("Multipath Control: " + action)
    mp_args = 'action ' + action
    if path_mgr:
        mp_args = [mp_args, 'pm ' + path_mgr]
    return adb_shell(False, uiautomator='multipath_control', args=mp_args)

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
    my_print("Router: exec: " + cmd)
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


##################################################
##             DEVICE: LAUNCH TESTS             ##
##################################################

adb_restart()

my_print("Check device is up")
for i in range(5): # check 5 time, max 30sec: should be enough
    adb_check_reboot()
    if LAST_UPTIME:
        break
    time.sleep(6)

if not LAST_UPTIME:
    my_print_err("Not able to contact the device... Stop")
    sys.exit(1)

if PURGE_TRACES_SMARTPHONE:
    my_print("Remove previous traces located on the phone")
    adb_shell("rm -r " + ANDROID_TRACE_OUT + "*")

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

TEST_NO = 1
NB_TESTS = len(Network) * len(mptcp) * len(uitests_dir)

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
        launch_all(uitests_dir, net.name, mptcp_dir)

        # Delete Netem
        if tc:
            disable_netem()

my_print("================ DONE =================\n")

if PURGE_TRACES_SMARTPHONE:
    my_print("Remove traces located on the phone")
    adb_shell("rm -r " + ANDROID_TRACE_OUT + "*")


my_print("Reboot the phone") # to avoid possible Android bugs
adb_reboot(wait=False)

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
