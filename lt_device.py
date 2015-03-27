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

from lt_tcp import TCP
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

# launch a command to the connected device
# cmd: command to launch (execpt if it's an uitest)
# uiautomator: name of the uitest to launch (if any)
# args: extra args for the uiautomator command
# out: return the output messages
# log: write output messages to an opened file descriptor
# quiet: don't print output to stdout/stderr
# restart: used to know if there are problems with ADB
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
    adb_cmd = ['adb', 'shell', full_cmd + '; echo -n $?']
    error = dev_not_found = False
    if out:
        result = []
    else:
        result = True

    if log:
        print(adb_cmd, file=log, flush=False)

    # adb shell doesn't return the last exit code, we need to analyse output
    # Note: We cannot use 'Proc.wait()': this will deadlock when using
    #       stdout=PIPE or stderr=PIPE and the child process generates enough
    #       output to a pipe such that it blocks waiting for the OS pipe buffer
    #       to accept more data. Solution: Popen.communicate()
    proc = subprocess.Popen(adb_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)

    # get data
    try:
        outs_line, errs_line = proc.communicate(timeout=s.TIMEOUT)
    except subprocess.TimeoutExpired:
        proc.kill()
        outs_line, errs_line = proc.communicate()
        my_print_err("Timeout when launching this command on the device: " + full_cmd)
        out = False # no need to append result
        error = True

    # stderr
    for line_err in errs_line.split('\n'):
        if line_err == 'error: device not found':
            dev_not_found = True

    if not quiet and errs_line:
        print(s.RED + errs_line + s.WHITE_ERR, file=sys.stderr)

    # stdout
    stdout = outs_line.split('\n')
    if uiautomator or out or not quiet:
        for line in stdout[:-1]: # without the return code
            if uiautomator and line.lower().startswith('failure'):
                error = True
                if not quiet:
                    print(s.RED + line + s.WHITE_ERR, file=sys.stderr)
            if out and not line.startswith('* daemon'):
                result.append(line)
            if not quiet and line:
                print(s.BLUE + line + s.WHITE_STD)

    if log:
        if errs_line:
            print('stderr: ' + errs_line + '\nstdout:\n', file=log, flush=False)
        print(outs_line, file=log, flush=False)

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

    last_line = stdout[-1]
    try:
        last_number = int(last_line)
    except ValueError as e:
        last_number = -1

    if last_number != 0:
        if not quiet:
            my_print_err("when launching this cmd on the device: " + full_cmd + " - last number: " + last_line)
        return False
    return result

def adb_shell_root(cmd):
    su_cmd = 'su sh -c "' + cmd + '"'
    return adb_shell(su_cmd)

# filename: name of the file or cmd + '.txt'
def adb_shell_write_output(cmd, out_dir=None, filename=False, verbose=False):
    my_print("Get " + cmd + " from smartphone")
    if out_dir:
        with open(os.path.join(out_dir, filename if filename else cmd.replace(' ', '_') + '.txt'), "w") as out_file:
            out = adb_shell(cmd, log=out_file, quiet=not verbose)
        return out
    else:
        return adb_shell(cmd, out=True)

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

def adb_reboot(wait=True, tcp_mode=None, net_name=None):
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
        success = False
        for i in range(5): # limit waiting time
            if i > 0 and not timeout:
                time.sleep(30*60)
            try:
                timeout = False
                if subprocess.call("adb wait-for-device".split(), timeout=1800) == 0:
                    success = True
                    break
            except:
                timeout = False
                my_print_err("Device not found... wait and retry " + str(i))
                if not adb_restart(): # restart: avoid permission problems
                    adb_restart_root() # try root if problem
        if not success:
            my_print_err("Device not found... EXIT")
            sys.exit(1)
        elif tcp_mode:
            return net.set_multipath_control_startup(tcp_mode, net_name)
        elif net_name:
            return net.set_rmnet_ip(net_name)
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

# min_size: if one file has less than min_size bytes, ALL files will now have ".err" as new extention.
def adb_pull_files(android_dir, out_dir_app, min_size=0, is_dir=True):
    my_print("Pull files to " + out_dir_app)
    cmd = "adb pull " + android_dir + ("/ " if is_dir else "") + out_dir_app
    if subprocess.call(cmd.split()) != 0:
        my_print_err("when pulling traces for " + android_dir)
    elif min_size:
        files_fullpath = adb_shell("ls " + android_dir + ("/" if is_dir else ""), out=True, quiet=True)
        if not files_fullpath:
            return False
        files = []
        # get basename
        for file in files_fullpath:
            # unix style, change that if you want to use Windows...
            files.append(os.path.join(out_dir_app, os.path.basename(file)))
        # get size
        has_error = False
        for file in files:
            if os.stat(file).st_size < min_size:
                has_error = True
                break
        # add .err
        if has_error:
            my_print_err("size lower than " + str(min_size) + " in: " + out_dir_app)
            for file in files:
                my_print_err("Rename " + file + " to " + file + ".err")
                os.rename(file, file + ".err")
            return False
    return True


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

def get_proxy_filters(rmnet_ip=False, out_dir=None, filename='proxy_filters.txt'):
    filters = "tcp and host " + s.EXTERNAL_IP
    if rmnet_ip:
        filters += " or host " + rmnet_ip
    if out_dir:
        with open(os.path.join(out_dir, filename), 'w') as out_file:
            print(filters, file=out_file)
    return filters


##################################################
##                DEVICE: CAPTURE               ##
##################################################

# Launch full capture on the server
def manage_capture_server(mode, arg_pcap=None):
    if not s.CAPTURE_ON_PROXY:
        return
    my_print("Send request to the server to " + mode + " a full capture")
    cmd = ["bash", mode + "_full_pcap_distant.sh"]
    if arg_pcap:
        cmd += arg_pcap.split()
    if subprocess.call(cmd) != 0:
        my_print_err("when using " + mode + "_full_pcap_distant.sh with " + str(arg_pcap))

def stop_capture_device():
    my_print("Stop capturing traces on the device")
    if not s.CAPTURE_ON_ANY and not s.CAPTURE_ON_LO:
        my_print("No tcpdump processes to stop")
        return True

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
    adb_shell('mkdir -p ' + android_pcap_dir)
    time.sleep(0.5)

    rc = True
    i = 1
    if s.CAPTURE_ON_ANY:
        tcp_filter = 'tcp'
        # To not have duplicated data on ANY and remove unwanted traffic
        if s.PROXY_IP:
            tcp_filter += ' and ip host ' + s.PROXY_IP
        if s.PROXY_PORT:
            tcp_filter += ' and port ' + str(s.PROXY_PORT)
        if net_name.startswith('wlan'):
            iface = "wlan0"
        elif net_name.startswith('rmnet'):
            iface = "rmnet0"
        else: # both
            iface = "any"
            tcp_filter += ' and not ip host 127.0.0.1'

        pcap_file = android_pcap_dir + '/' + arg_pcap + '_' + iface + '.pcap'
        cmd = 'tcpdump -i ' + iface + ' -w ' + pcap_file + ' ' + tcp_filter + ' &'

        if not launch_capture_device(cmd, i):
            my_print_err("Not able to start tcpdump!")
            rc = False
        else:
            i += 1

    if s.CAPTURE_ON_LO and (s.WITH_SSH_TUNNEL or s.WITH_SHADOWSOCKS):
        pcap_file_lo = android_pcap_dir + '/' + arg_pcap + '_lo.pcap'
        port_no = s.SSHTUNNEL_PORT if s.WITH_SSH_TUNNEL else s.SHADOWSOCKS_PORT
        # filter internal port used by the proxy and all communications between two 127.0.0.1 (mostly DNS and TCP Reset)
        cmd_lo = 'tcpdump -i lo -w ' + pcap_file_lo + ' tcp and not port ' + str(port_no) + ' and not \(src 127.0.0.1 and dst 127.0.0.1\) &'
        if not launch_capture_device(cmd_lo, i):
            my_print_err("Not able to start tcpdump for LoopBack only!")
            stop_capture_device()
            rc = False

    return rc

# Launch/Stop full capture on the server and on the device, then restart/stop proxy
def manage_capture(start, arg_pcap, server_pcap_dir, android_pcap_dir, net_name, rm=False, filters='tcp'):
    arg_pcap_path = server_pcap_dir + '/' + arg_pcap + '_server'

    if start: # first the server, then the device
        manage_capture_server("start_" + ("sshtunnel" if s.WITH_SSH_TUNNEL else "shadowsocks"), arg_pcap_path + " " + filters)
        if not start_capture_device(arg_pcap, android_pcap_dir, net_name):
            manage_capture_server("stop", arg_pcap_path)
            manage_capture_server("rm", arg_pcap_path)
            return False
        if not restart_proxy():
            stop_capture_device()
            adb_shell('rm -rf ' + android_pcap_dir)
            manage_capture_server("stop", arg_pcap_path)
            manage_capture_server("rm", arg_pcap_path)
            return False
        return True
    else:
        success = stop_proxy()
        stop_capture_device()
        manage_capture_server("stop", arg_pcap_path)
        if rm:
            manage_capture_server("rm", arg_pcap_path)
            adb_shell('rm -rf ' + android_pcap_dir)
        return success


##################################################
##               DEVICE: GET INFO               ##
##################################################

def get_info_netcfg(out_dir=None, filename=False):
    return adb_shell_write_output('netcfg', out_dir, filename)

def get_info_netstat(out_dir=None, filename=False):
    return adb_shell_write_output('netstat', out_dir, filename)

def get_info_mptcp(out_dir=None, filename='mptcp.txt'):
    return adb_shell_write_output('cat /proc/net/mptcp', out_dir, filename)

def get_info_mptcp_fm(out_dir=None, filename='mptcp_fm.txt'):
    return adb_shell_write_output('cat /proc/net/mptcp_fullmesh', out_dir, filename)

def get_info_wifi(out_dir=None, filename='dumpsys_wifi.txt'):
    return adb_shell_write_output('dumpsys wifi | grep -e "^  " -e "mWifiInfo:"', out_dir, filename)

def get_info_wifi_power_header():
    return 'SSID,BSSID,MAC,RSSI,LINK'

def get_info_wifi_power():
    out = adb_shell_write_output('dumpsys wifi | grep "mWifiInfo:"')
    try:
        out = out[0][12:-1].split(',')
        ssid = out[0][6:]
        bssid = out[1][8:]
        mac = out[2][6:]
        rssi = out[4][7:]
        link = out[5][13:]
        return '{},{},{},{},{}'.format(ssid, bssid, mac, rssi, link)
    except:
        return ',,,0,0'

def get_info_rmnet(out_dir=None, filename='dumpsys_rmnet.txt'):
    """ It will return: Gsm Signal Strength, Gsm Bit Error Rate, CDMA Dbm,
        CDMA Ecio, Evdo Dbm, Evdo Ecio, Evdo Snr, LTE Signal Strength, LTE Rsrp,
        LTE Rsrq, LTE Rssnr, LTE Cqi, "gsm|lte" or "cdma"

        About Signal Strength, defined values:
            <rssi> : integer type
            0      : -113 dBm or less
            1      : -111 dBm
            2...30 : -109... -53 dBm ==> -2dBm
            31     : -51 dBm or greater
            99     : not known or not detectable

        Details: https://developer.android.com/reference/android/telephony/SignalStrength.html
    """
    return adb_shell_write_output('dumpsys telephony.registry | grep mSignalStrength', out_dir, filename)

def get_info_rmnet_power_header():
    return 'gsm signal strenght,gsm bit error rate,cdma dbm,cdma ecio,' \
         + 'evdo dbm,evdo ecio,evdo snr,lte signal strength,lte rsrp,' \
         + 'lte rsrq,lte rssnr,lte cqi,protocol'

def get_info_rmnet_power():
    out = get_info_rmnet()
    try:
        return out[0][34:].replace(' ', ',')
    except:
        return '99,0,-120,-160,-120,-1,-1,99,-99,0,0,gsm|lte'

def get_info_sysctl_tcp(out_dir=None, filename='sysctl_tcp.txt'):
    return adb_shell_write_output('sysctl net 2> /dev/null | grep tcp', out_dir, filename)

def get_info_sysctl_mptcp_only(out_dir=None, filename='sysctl_mptcp.txt'):
    return adb_shell_write_output('sysctl net.mptcp', out_dir, filename)


##################################################
##                DEVICE: LAUNCH                ##
##################################################

# Launch test for one app and pull files after each test (if there is a bug)
#  func_init function will be launched with current args in the current thread just before func_start
#  func_start function will be launched with current args in a new thread just before launching tests.
#  func_end will be launched with current args + success in the current thread just after the end of the test.
#  func_exit will be launched with current args + thread in the current thread after having stopped capturing traces
def launch(app, net_name, tcp_mode, out_dir, func_init=False, func_start=False, func_end=False, func_exit=False, uitests_args=False, filters='tcp'):
    time_now = time.strftime("%Y%m%d-%H%M%S")
    out_dir_app = os.path.abspath(os.path.join(out_dir, app)) # mptcp/net_name/app
    arg_pcap = str(tcp_mode).lower() + "_" + app + "_" + net_name + "_" + time_now
    unix_pcap_dir = str(tcp_mode) + '/' + net_name + '/' + app # unix, not used os.path.join
    server_pcap_dir = g.SAVE_DIR + '/' + unix_pcap_dir
    android_pcap_dir = s.ANDROID_TRACE_OUT + '/' + unix_pcap_dir

    # Create dir and put netstat info + pcap in it
    if not os.path.isdir(out_dir_app):
        os.makedirs(out_dir_app)

    # Start full capture on the proxy and on the device
    if not manage_capture(True, arg_pcap, server_pcap_dir, android_pcap_dir, net_name, filters=filters):
        my_print_err("Error proxy: Skip test of " + app.upper())
        return False

    get_info_netstat(out_dir_app, filename='netstat_before.txt')
    get_info_mptcp(out_dir_app, filename='mptcp_before.txt')
    get_info_mptcp_fm(out_dir_app, filename='mptcp_fm_before.txt')

    if func_init:
        func_init(*(app, net_name, tcp_mode, out_dir))

    if func_start:
        thread = threading.Thread(target=func_start, args=(app, net_name, tcp_mode, out_dir))
        thread.start()
    elif func_exit:
        thread = None

    my_print("*** Launching tests " + str(g.TEST_NO) + '/' + str(g.NB_TESTS) + " for [ " + s.YELLOW + app.upper() + s.GREEN + " ] at " + time_now + " for " + net_name + " ***")
    with open(os.path.join(out_dir_app, 'uitests.log'), "w") as log_file:
        success = adb_shell(False, uiautomator=app, log=log_file, args=uitests_args)

    if func_end:
        func_end(*(app, net_name, tcp_mode, out_dir, success))

    get_info_netstat(out_dir_app, filename='netstat_after.txt')
    get_info_mptcp(out_dir_app, filename='mptcp_after.txt')
    get_info_mptcp_fm(out_dir_app, filename='mptcp_fm_after.txt')

    # Kill the app
    pkg_name_file = os.path.join("uitests-" + app, "pkg_name.txt")
    try:
        file = open(pkg_name_file, 'r')
        pkg_name = file.readlines()[0].replace('\n', '')
        file.close()
        my_print("Force stop app " + app + " - " + pkg_name)
        adb_shell("am kill " + pkg_name) # should be soft kill
        time.sleep(0.5)
        adb_shell("am force-stop " + pkg_name) # to be sure that nothing more is running
        adb_shell_root("rm -rf /data/data/" + pkg_name + "/cache/*")
    except:
        my_print_err("Not able to find pkg name and then kill " + app)

    # Stop full capture on the proxy and on the device
    manage_capture(False, arg_pcap, server_pcap_dir, android_pcap_dir, net_name, not success)

    if func_exit:
        func_exit(*(app, net_name, tcp_mode, out_dir, thread))

    # no need to pull useless and removed traces
    if not success:
        return False

    # Save files: 'traces' external dir already contains the app name
    return adb_pull_files(android_pcap_dir, out_dir_app, min_size=1000)
    # Files will be saved in ~/Thesis/TCPDump/DATE-HOUR-SHA1/MPTCP/NET/APP/MPTCP_APP_NET_DATE_HOUR.pcap + MPTCP_APP_NET_DATE_HOUR_lo.pcap

def launch_all(uitests_dir, net_name, tcp_mode, out_base, func_init=False, func_start=False, func_end=False, func_exit=False, uitests_args=False):
    # out_dir: ~/Thesis/TCPDump/DATE-HOUR-SHA1/MPTCP/NET
    out_dir = os.path.join(out_base, str(tcp_mode), net_name)
    if (not os.path.isdir(out_dir)):
        os.makedirs(out_dir)

    # Generate seed
    my_print("Generate seed")
    subprocess.call(['./generate_push_random_seed.sh'])

    # random: to avoid having the same order
    random.shuffle(uitests_dir)
    my_print("Launch all tests for " + net_name + " with random list: " + str(uitests_dir))

    get_info_netcfg(out_dir)
    get_info_netstat(out_dir)
    get_info_wifi(out_dir)
    get_info_rmnet(out_dir)
    get_info_sysctl_tcp(out_dir)
    filters = get_proxy_filters(g.RMNET_IP, out_dir)

    for uitest in uitests_dir:
        app = uitest[8:]
        # launch one + retry if needed
        for i in range(s.LAUNCH_RETRY_MAX + 1):
            time_before = time.time()
            success = launch(app, net_name, tcp_mode, out_dir, func_init, func_start, func_end, func_exit, uitests_args, filters)
            my_print('UITest ' + str(g.TEST_NO) + '/' + str(g.NB_TESTS) + ' (' + str(i) + ') for ' + app + ' took ' + str(round(time.time() - time_before)) + ' seconds')
            if success:
                break
            elif s.LAUNCH_RETRY_MAX > 0 and i % 2 == 1 and i < s.LAUNCH_RETRY_MAX:
                my_print_err("Not able to get good results after " + str(i+1) + "tries, reboot, wait and retry")
                adb_reboot(wait=True, tcp_mode=tcp_mode, net_name=net_name)
        g.TEST_NO += 1

    # Compress files
    my_print("Compressing files")
    for app in os.listdir(out_dir):
        app_dir = os.path.abspath(os.path.join(out_dir, app))
        if not os.path.isdir(app_dir): # we can have pid files
            continue
        for trace in os.listdir(app_dir):
            if trace.endswith('.pcap') or trace.endswith('.pcap.err'):
                trace_path = os.path.join(app_dir, trace)
                if os.path.exists(trace_path + '.gz'):
                    my_print_err("This file is already compressed! " + trace_path)
                my_print("Compressing " + trace_path + " to " + trace_path + ".gz")
                cmd = 'gzip -9 -f ' + trace_path # or xz/7z format?
                if subprocess.call(cmd.split()) != 0:
                    my_print_err(" when pulling traces for " + app)
