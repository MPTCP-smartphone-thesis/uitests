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
import random
import subprocess
import sys
import time
import threading

import lt_settings as s
import lt_globals as g

from lt_utils import *

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
        proc.wait(s.TIMEOUT)
    except:
        my_print_err("(timeout) when launching this cmd on the device: " + str(proc.args))
        proc.terminate()

def adb_shell(cmd, uiautomator=False, args=False, out=False, log=False, quiet=False, restart=0):
    if uiautomator:
        full_cmd = "uiautomator runtest " + s.ANDROID_HOME + "/uitests-" + uiautomator + ".jar -c " + uiautomator + ".LaunchSettings"
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

    if log:
        print(adb_cmd, file=log, flush=False)

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
            if not quiet:
                print(s.RED + line_err_strip + s.WHITE_ERR, file=sys.stderr)
            if log:
                print('stderr: ' + line_err_strip, file=log, flush=False)

        line = proc.stdout.readline()
        if line:
            last_line = line.rstrip()
            if uiautomator and last_line.lower().startswith('failure'):
                error = True
                if not quiet:
                    print(s.RED + last_line + s.WHITE_ERR, file=sys.stderr)
            if out and not last_line.startswith('* daemon'):
                result.append(last_line)
            if not quiet:
                print(s.BLUE + last_line + s.WHITE_STD)
            # check number if last line (exit code)
            if len(last_line) < 4:
                try:
                    number = int(last_line)
                    if number >= 0 or number <= 255:
                        last_number = number
                except ValueError as e:
                    pass
            if log:
                print(last_line, file=log, flush=False)

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
        return adb_shell(cmd, uiautomator, args, out, log, quiet, restart+1)

    rc = proc.returncode
    if rc != 0 or error:
        if not quiet:
            my_print_err("when launching this cmd on the device: " + full_cmd + " - rc: " + str(rc))
        return False

    if last_number != 0:
        if not quiet:
            my_print_err("when launching this cmd on the device: " + full_cmd + " - last number: " + last_line)
        return False
    return result

def adb_shell_root(cmd):
    su_cmd = 'su sh -c "' + cmd + '"'
    return adb_shell(su_cmd)

# filename: name of the file or cmd + '.txt'
def adb_shell_write_output(cmd, out_dir, filename=False, verbose=False):
    my_print("Get " + cmd + " from smartphone")
    with open(os.path.join(out_dir, filename if filename else cmd.replace(' ', '_') + '.txt'), "w") as out_file:
        out = adb_shell(cmd, log=out_file, quiet=not verbose)

def adb_get_uptime():
    up_out = adb_shell("uptime", out=True)
    try:
        return time.strptime(up_out[0][9:17], "%H:%M:%S")
    except:
        my_print_err("Not able to get the uptime")
        return False

# return True if has rebooted or error
def adb_check_reboot():
    uptime = adb_get_uptime()
    if not uptime: return True

    old_up = g.LAST_UPTIME
    g.LAST_UPTIME = uptime

    return old_up > uptime # True if old == ()

# return True if it has rebooted
def adb_check_reboot_sim():
    my_print("Check if we have 'SIM card added' warning")
    rebooted = False
    # SIM warning
    while adb_shell(False, uiautomator='kill_app', args='sim true', quiet=True): # hide error
        my_print("Wait: the smartphone is rebooting")
        time.sleep(60)
        rebooted = True

    up = adb_check_reboot()
    if g.LAST_UPTIME and g.LAST_UPTIME < time.strptime("45", "%S"):
        my_print("Uptime is lower than 45 sec, wait 30 seconds more")
        time.sleep(30)
    return rebooted or up or not g.LAST_UPTIME

def adb_reboot(wait=True):
    if not s.ADB_REBOOT:
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
    ps_out = adb_shell('ps | grep ' + proc_name, out=True, quiet=True)
    if ps_out:
        output = []
        for line in ps_out:
            if strict and line.endswith(proc_name) or not strict and proc_name in line:
                output.append(line.split()[1])
        return output
    return []


##################################################
##                 DEVICE: PROXY                ##
##################################################

# relaunch SSH-Tunnel and check the connection via a ping
def restart_proxy(sleep=1):
    if not s.WITH_SSH_TUNNEL:
        return True

    my_print("Restart proxy: ping")
    if s.EXT_HOST:
        cmd_ping = "ping -c 4 " + s.EXT_HOST
        adb_shell(cmd_ping) ## to avoid strange DNS problems

    my_print("Restart proxy: ssh tunnel")
    if not adb_shell(False, uiautomator='ssh_tunnel'): return False

    if s.EXT_HOST:
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
    if not s.WITH_SSH_TUNNEL:
        return True

    my_print("Stop proxy")
    return adb_shell(False, uiautomator='ssh_tunnel', args='action stop')


##################################################
##                DEVICE: CAPTURE               ##
##################################################

# Launch full capture on the server
def manage_capture_server(mode, arg_pcap):
    if not s.CAPTURE_ON_PROXY:
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
            my_print_err("Not able to launch tcpdump")
            return False
        i += 1
        adb_shell_root(cmd)
        time.sleep(1)
        pids = adb_get_pid('tcpdump')
    return True

def start_capture_device(arg_pcap, android_pcap_dir, net_name):
    my_print("Capture traces on the device")
    tcp_filter = 'tcp'
    if net_name.startswith('wlan'):
        iface = "wlan0"
    elif net_name.startswith('rmnet'):
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

    if not s.WITH_SSH_TUNNEL and not s.WITH_SHADOWSOCKS:
        return True

    pcap_file_lo = android_pcap_dir + '/' + arg_pcap + '_lo.pcap'
    port_no = s.SSHTUNNEL_PORT if s.WITH_SSH_TUNNEL else s.SHADOWSOCKS_PORT
    cmd_lo = 'tcpdump -i lo -w ' + pcap_file_lo + ' tcp and not port ' + str(port_no) + ' &'
    if not launch_capture_device(cmd_lo, 2):
        my_print_err("Not able to start tcpdump for LoopBack only!")
        stop_capture_device()
        return False
    return True

# Launch/Stop full capture on the server and on the device, then restart/stop proxy
def manage_capture(start, mptcp_dir, app, android_pcap_dir, net_name, time_now, rm=False):
    arg_pcap = mptcp_dir.lower() + "_" + app + "_" + net_name + "_" + time_now

    if start: # first the server, then the device
        manage_capture_server("start_sshtunnel" if s.WITH_SSH_TUNNEL else "start_shadowsocks", arg_pcap)
        if not start_capture_device(arg_pcap, android_pcap_dir, net_name):
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


##################################################
##                DEVICE: LAUNCH                ##
##################################################

# Launch test for one app and pull files after each test (if there is a bug)
#  func_init function will be launched with current args in the current thread just before func_start
#  func_start function will be launched with current args in a new thread just before launching tests.
#  func_end will be launched with current args + success in the current thread just after the end of the test.
#  func_exit will be launched with current args + thread in the current thread after having stopped capturing traces
def launch(app, net_name, mptcp_dir, out_dir, func_init=False, func_start=False, func_end=False, func_exit=False, uitests_args=False):
    time_now = time.strftime("%Y%m%d-%H%M%S")
    out_dir_app = os.path.abspath(os.path.join(out_dir, app)) # mptcp/net_name/app
    android_pcap_dir = s.ANDROID_TRACE_OUT + '/' + mptcp_dir + '/' + net_name + '/' + app

    # Create dir and put netstat info + pcap in it
    if not os.path.isdir(out_dir_app):
        os.makedirs(out_dir_app)

    # Start full capture on the proxy and on the device
    if not manage_capture(True, mptcp_dir, app, android_pcap_dir, net_name, time_now):
        my_print_err("Error proxy: Skip test of " + app.upper())
        return

    adb_shell_write_output('netstat', out_dir_app, filename='netstat_before.txt')

    if func_init:
        func_init(*(app, net_name, mptcp_dir, out_dir))

    if func_start:
        thread = threading.Thread(target=func_start, args=(app, net_name, mptcp_dir, out_dir))
        thread.start()
    elif func_exit:
        thread = None

    my_print("*** Launching tests for [ " + s.YELLOW + app.upper() + s.GREEN + " ] at " + time_now + " for " + net_name + " ***")
    with open(os.path.join(out_dir_app, 'uitests.log'), "w") as log_file:
        success = adb_shell(False, uiautomator=app, log=log_file, args=uitests_args)

    if func_end:
        func_end(*(app, net_name, mptcp_dir, out_dir, success))

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
    manage_capture(False, mptcp_dir, app, android_pcap_dir, net_name, time_now, not success)

    if func_exit:
        func_exit(*(app, net_name, mptcp_dir, out_dir, thread))

    # no need to pull useless traces
    if not success:
        my_print("Error during the test, remove traces")
        cmd = "rm -rf " + android_pcap_dir
        adb_shell(cmd)
        return False

    # Save files: 'traces' external dir already contains the app name
    my_print("Pull files to " + out_dir_app)
    cmd = "adb pull " + android_pcap_dir + "/ " + out_dir_app
    if subprocess.call(cmd.split()) != 0:
        my_print_err("when pulling traces for " + app)
    # Files will be saved in ~/Thesis/TCPDump/DATE-HOUR-SHA1/MPTCP/NET/APP/MPTCP_APP_NET_DATE_HOUR.pcap + MPTCP_APP_NET_DATE_HOUR_lo.pcap

def launch_all(uitests_dir, net_name, mptcp_dir, out_base, func_init=False, func_start=False, func_end=False, func_exit=False, uitests_args=False):
    # out_dir: ~/Thesis/TCPDump/DATE-HOUR-SHA1/MPTCP/NET
    out_dir = os.path.join(out_base, mptcp_dir, net_name)
    if (not os.path.isdir(out_dir)):
        os.makedirs(out_dir)

    # Generate seed
    my_print("Generate seed")
    subprocess.call(['./generate_push_random_seed.sh'])

    # random: to avoid having the same order
    random.shuffle(uitests_dir)
    my_print("Launch all tests for " + net_name + " with random list: " + str(uitests_dir))

    adb_shell_write_output('netcfg', out_dir)
    adb_shell_write_output('netstat', out_dir)

    for uitest in uitests_dir:
        app = uitest[8:]
        time_before = time.time()
        launch(app, net_name, mptcp_dir, out_dir, func_init, func_start, func_end, func_exit, uitests_args)
        my_print('UITest ' + str(g.TEST_NO) + '/' + str(g.NB_TESTS) + ' for ' + app + ' took ' + str(round(time.time() - time_before)) + ' seconds')
        g.TEST_NO += 1

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
                cmd = 'gzip -9 -f ' + trace_path # or xz/7z format?
                if subprocess.call(cmd.split()) != 0:
                    my_print_err(" when pulling traces for " + app)
