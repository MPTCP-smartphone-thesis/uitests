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

import subprocess
import time

import lt_settings as s
import lt_device as dev

from lt_utils import * # my_print

## Net: devices
WIFI = 'wifi'
DATA = 'data'
WLAN = 'wlan0'
RMNET = 'rmnet0'


##################################################
##            DEVICE: NETWORK IFACES            ##
##################################################

# version should be: '4', '3' or '2'
def change_pref_net(version):
    my_print("Settings: prefer " + version + "G")
    arg = "network-status " + version + "G"
    return dev.adb_shell(False, uiautomator='preference_network', args=arg)

def avoid_poor_connections(enable):
    my_print("Settings: avoid poor connections: " + str(enable))
    arg = "avoid-poor-conn " + ("on" if enable else "off")
    return dev.adb_shell(False, uiautomator='preference_network', args=arg)

# 'wifi', 'enable'
def manage_net(iface, status):
    my_print(status + " " + iface)
    return dev.adb_shell_root('svc ' + iface + ' ' + status)

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


##################################################
##          DEVICE: NETWORK IP/ROUTES           ##
##################################################

def get_ipv4(iface):
    ip = dev.adb_shell('ip addr show ' + iface, out=True, quiet=True)
    if ip and len(ip) > 2:
        try: # 3th line: '    inet 37.62.66.XXX/29 scope global rmnet0'
            return ip[2].split()[1][:-3]
        except:
            return False
    return False

def get_all_ipv4():
    result = {}
    for iface in (WLAN, RMNET):
        addr = get_ipv4(iface)
        if addr:
            result[iface] = addr
    return result

ROUTE_CMD = 'ip route show scope link proto boot table main'
def get_route(iface, route=False):
    if not route:
        route = dev.adb_shell(ROUTE_CMD, out=True, quiet=True)
    if route:
        for line in route:
            if iface in line and not '/' in line:
                return line.split()[0]
    return False

def get_all_route():
    result = {}
    route = dev.adb_shell(ROUTE_CMD, out=True, quiet=True)
    for iface in (WLAN, RMNET):
        addr = get_route(iface, route)
        if addr:
            result[iface] = addr
    return result

# get a tuple: [iface, ip] => ('wlan0', '192.168.0.1')
def get_default_route():
    route = dev.adb_shell('ip route list 0/0', out=True, quiet=True)
    if route:
        try: # default via 192.168.0.1 dev wlan0
            route_split = route[0].split()
            return (route_split[4], route_split[2])
        except:
            return False
    return route

def change_default_route(iface, addr):
    my_print("Default route to " + iface + " - " + addr)
    success = dev.adb_shell_root('ip route change default via ' + addr + ' dev ' + iface)
    if success:
        return success
    # try by adding a new default route
    return dev.adb_shell_root('ip route add default via ' + addr + ' dev ' + iface)

def change_default_route_wlan():
    addr = get_route(WLAN)
    if addr:
        return change_default_route(WLAN, addr)
    return False

def change_default_route_rmnet():
    addr = get_route(RMNET)
    if addr:
        return change_default_route(RMNET, addr)
    return False


##################################################
##              DEVICE: MULTIPATH               ##
##################################################

def sysctl_mptcp(key, value):
    arg = "net.mptcp.mptcp_" + key + "=" + value
    my_print("Sysctl: " + arg)
    return dev.adb_shell_root("sysctl -w " + arg)

def iproute_set_multipath(iface, status):
    my_print("Multipath: status " + status + " for " + iface)
    return dev.adb_shell_root("ip link set dev " + iface + " multipath " + status)

def iproute_set_multipath_off_wlan():
    return iproute_set_multipath(WLAN, 'off')

def iproute_set_multipath_off_rmnet():
    return iproute_set_multipath(RMNET, 'off')

def iproute_set_multipath_off():
    rc = iproute_set_multipath_off_wlan()
    rc &= iproute_set_multipath_off_rmnet()
    return rc

def iproute_set_multipath_on_wlan():
    return iproute_set_multipath(WLAN, 'on')

def iproute_set_multipath_on_rmnet():
    return iproute_set_multipath(RMNET, 'on')

def iproute_set_multipath_on():
    rc = iproute_set_multipath_on_wlan()
    rc &= iproute_set_multipath_on_rmnet()
    return rc

def iproute_set_multipath_backup_wlan(route=True):
    rc = iproute_set_multipath(WLAN, 'backup')
    rc &= iproute_set_multipath_on_rmnet()
    if route:
        rc &= change_default_route_rmnet()
    return rc

def iproute_set_multipath_backup_rmnet(route=True):
    rc = iproute_set_multipath(RMNET, 'backup')
    rc &= iproute_set_multipath_on_wlan()
    if route:
        rc &= change_default_route_wlan()
    return rc

def mptcp_path_manager(path_mgr='default'):
    return sysctl_mptcp('path_manager', path_mgr)

def mptcp_round_robin(enable=True):
    return sysctl_mptcp('scheduler', 'roundrobin' if enable else 'default')

# 'enable' or 'disable'
def multipath_control(action='enable', path_mgr='default', rr=False):
    dev.stop_proxy() ## prevent error when enabling mptcp
    my_print("Multipath Control: " + action)
    rc = dev.adb_shell(False, uiautomator='multipath_control', args='action ' + action)
    rc &= mptcp_path_manager(path_mgr)
    rc &= mptcp_round_robin(rr)
    return rc

def multipath_control_fullmesh(action='enable', backup=False, rr=False):
    rc = multipath_control(action, path_mgr='fullmesh', rr=rr)
    if s.IPROUTE_WITH_MULTIPATH:
        if backup:
            rc &= iproute_set_multipath_backup_rmnet()
        else:
            rc &= iproute_set_multipath_on()
    return rc

def ndiffports_set_subflows(subflows):
    my_print("NDiffPorts set subflows: " + str(subflows))
    cmd = 'echo ' + str(subflows) + ' > /sys/module/mptcp_ndiffports/parameters/num_subflows'
    return dev.adb_shell_root(cmd)

def multipath_control_ndiffports(action='enable', subflows=s.NDIFFPORTS_DEFAULT_NB):
    rc = multipath_control(action, path_mgr='ndiffports')
    rc &= ndiffports_set_subflows(subflows)
    return rc


##################################################
##                    ROUTER                    ##
##################################################

def router_shell(cmd, ips=s.IP_ROUTER):
    my_print("Router: exec: " + cmd)
    rc = True
    sshpass = ("sshpass -p " + s.PASSWORD_ROUTER + " ") if s.PASSWORD_ROUTER else ""
    for ip in ips:
        router_cmd = sshpass + "ssh " + s.USER_ROUTER + "@" + ip + " " + cmd
        if subprocess.call(router_cmd.split()) != 0:
            my_print_err("when launching this cmd '" + cmd + "' on the router " + ip)
            rc = False
    return rc

def router_send_file(file, chmod=False, ips=s.IP_ROUTER):
    my_print("Router: send: " + file)
    rc = True
    sshpass = ("sshpass -p " + s.PASSWORD_ROUTER + " ") if s.PASSWORD_ROUTER else ""
    for ip in ips:
        router_cmd = sshpass + "scp " + file + " " + s.USER_ROUTER + "@" + ip + ":."
        if subprocess.call(router_cmd.split()) != 0:
            my_print_err("when sending this file '" + file + "' on the router " + ip)
            rc = False
    if chmod:
        rc &= router_shell("chmod " + chmod + " " + file) # os.path.basename
    return rc

def get_value_between(string, start, end):
    index = string.find(start)
    if index >= 0:
        return string[index+1:string.index(end, index+1)]
    return False

def loss_cmd(value):
    if value:
        return " loss " + str(value) + "% " + str(int(value)/10) + "%"
    return ""

def delay_cmd(value):
    if value:
        return " delay " + str(value) + "ms " + str(int(value)/10) + "ms"
    return ""

def rate_cmd(value):
    if value:
        return " rate " + str(value) + "kbit"
    return ""

# user: 'root' or X for parent 1:X
def manage_netem(status, netem, user='root', ifaces=s.IFACE_ROUTER):
    rc = True
    for iface in ifaces:
        if user == 'root':
            u = user
        else:
            u = 'parent 1:' + str(user + i)
        cmd = "tc qdisc " + status + " dev " + iface + " " + u + " netem " + netem
        rc &= router_shell(cmd)
    return rc

def enable_netem(netem, user='root', ifaces=s.IFACE_ROUTER):
    return manage_netem('add', netem, user, ifaces)

def enable_netem_loss(value, user='root'):
    return enable_netem(loss_cmd(value), user)

def enable_netem_delay(value, user='root'):
    return enable_netem(delay_cmd(value), user)

def enable_netem_loss_delay(loss, delay, user='root'):
    return enable_netem(loss_cmd(value) + delay_cmd(value), user)

def enable_netem_var(case, value1, value2=0, user='root'):
    if case == 'loss':
        return enable_netem_loss(value1, user)
    elif case == 'delay':
        return enable_netem_delay(value1, user)
    elif case == 'both':
        return enable_netem_loss_delay(value1, value2, user)
    else:
        my_print_err("enable_netem_var: case unknown - " + str(case))
        return False

def change_netem(netem, user='root'):
    return manage_netem('change', netem, user)

def change_netem_loss(value, user='root'):
    return change_netem(loss_cmd(value), user)

def change_netem_delay(value, user='root'):
    return change_netem(delay_cmd(value), user)

def change_netem_loss_delay(loss, delay, user='root'):
    return change_netem(loss_cmd(loss) + delay_cmd(delay), user)

def change_netem_var(case, value1, value2=0, user='root'):
    if case == 'loss':
        return change_netem_loss(value1, user)
    elif case == 'delay':
        return change_netem_delay(value1, user)
    elif case == 'both':
        return change_netem_loss_delay(value1, value2, user)
    else:
        my_print_err("change_netem_var: case unknown - " + str(case))
        return False

def limit_bw_netem(bw, default=12):
    rc = True
    for iface in s.IFACE_ROUTER:
        cmd = 'tc qdisc add dev ' + iface + ' root handle 1: htb default ' + str(default)
        rc &= router_shell(cmd)
        cmd = 'tc class add dev ' + iface + ' parent 1:1 classid 1:' + str(default) + ' htb rate ' + str(bw) + ' ceil ' + str(bw)
        rc &= router_shell(cmd)
    return rc

def disable_netem():
    rc = True
    for iface in s.IFACE_ROUTER:
        rc &= router_shell("tc qdisc delete dev " + iface + " root")
    return rc

def reboot_router(wait=45):
    rc = router_shell('reboot')
    if wait:
        my_print('The router is rebooting, wait ' + str(wait) + ' seconds')
        time.sleep(wait)
    return rc

# WShaper: work fine alone, not dynamic (with delay, losses)

def limit_bw_wshaper_start():
    return router_shell('/etc/init.d/wshaper start')

def limit_bw_wshaper_stop():
    return router_shell('/etc/init.d/wshaper stop')

def limit_bw_wshaper_restart():
    rc =  limit_bw_wshaper_stop()
    rc &= limit_bw_wshaper_start()
    return rc

def limit_bw_wshaper(up, down, iface='wan', start=True):
    uci = 'uci set wshaper.settings.'
    rc  = router_shell(uci + 'network=' + iface)
    rc &= router_shell(uci + 'uplink=' + str(up))
    rc &= router_shell(uci + 'downlink=' + str(down))
    rc &= router_shell('uci commit wshaper')
    rc &= limit_bw_wshaper_start() if start else limit_bw_wshaper_stop()
    return rc

def unlimit_bw_wshaper():
    return limit_bw_wshaper(0, 0, start=False) # set up/down to 0 if reboot

# Our Shaper script: can manage delay/losses and change them dynamically

def shaper_start(up, down, netem=False, iface=s.WAN_IFACE, ips=s.IP_ROUTER):
    cmd = './shaper.sh start ' + iface + ' ' + str(up) + ' ' + str(down) + ' ' + (netem if netem else '')
    return router_shell(cmd, ips=ips)

def shaper_stop(iface=s.WAN_IFACE):
    return router_shell('./shaper.sh stop ' + iface)

def shaper_enable_netem(netem, iface=s.WAN_IFACE):
    return router_shell('./shaper.sh addnetem ' + iface + ' ' + netem)

def shaper_enable_netem_var(case, value1, value2=0, iface=s.WAN_IFACE):
    if case == 'loss':
        return shaper_enable_netem(loss_cmd(value1), iface=iface)
    elif case == 'delay':
        return shaper_enable_netem(delay_cmd(value1), iface=iface)
    elif case == 'both':
        return shaper_enable_netem(loss_cmd(value1) + delay_cmd(value2), iface=iface)
    else:
        my_print_err("shaper_add_netem_var: case unknown - " + str(case))
        return False

def shaper_change_netem(netem, iface=s.WAN_IFACE):
    return router_shell('./shaper.sh chnetem ' + iface + ' ' + netem)

def shaper_change_netem_var(case, value1, value2=0, iface=s.WAN_IFACE):
    if case == 'loss':
        return shaper_change_netem(loss_cmd(value1), iface=iface)
    elif case == 'delay':
        return shaper_change_netem(delay_cmd(value1), iface=iface)
    elif case == 'both':
        return shaper_change_netem(loss_cmd(value1) + delay_cmd(value2), iface=iface)
    else:
        my_print_err("shaper_change_netem_var: case unknown - " + str(case))
        return False

def shaper_change_bw(up, down, iface=s.WAN_IFACE):
    return router_shell('./shaper.sh chbw ' + iface + ' ' + str(up) + ' ' + str(down))

# Wireless

def manage_iw(status):
    rc = True
    for iface in s.DEVICES_ROUTER:
        cmd = 'iw phy ' + iface + ' set ' + status
        rc &= router_shell(cmd)
    return rc

# value < 30.0
def set_wlan_power(value='auto'):
    """ Value is in dBm, an exponential scale! P [mW] = 10 ^ (P [dBm] / 10) """
    if value == 'auto':
        status = value
    else:
        status = 'fixed ' + str(value)
    return manage_iw('txpower ' + status)

# will be launched on the machine
def get_external_ip():
    ip = subprocess.check_output('dig +short myip.opendns.com @resolver1.opendns.com'.split(), universal_newlines=True)
    if ip:
        return ip[:-1] # without the new line
    return ip
