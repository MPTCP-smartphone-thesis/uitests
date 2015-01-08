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

import lt_settings as s
import lt_device as dev

from lt_utils import * # my_print

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

# 'enable' or 'disable'
def multipath_control(action, path_mgr=False):
    dev.stop_proxy() ## prevent error when enabling mptcp
    my_print("Multipath Control: " + action)
    mp_args = 'action ' + action
    if path_mgr:
        mp_args = [mp_args, 'pm ' + path_mgr]
    return dev.adb_shell(False, uiautomator='multipath_control', args=mp_args)

## Net: router

def get_value_between(string, start, end):
    index = string.find(start)
    if index >= 0:
        return string[index+1:string.index(end, index+1)]
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
    router_cmd = ["sshpass", "-p " + s.PASSWORD_ROUTER, "ssh " + s.USER_ROUTER + "@" + s.IP_ROUTER, cmd]
    if subprocess.call(router_cmd) != 0:
        my_print_err("when launching this cmd on the router: " + cmd)
        return False
    return True

def manage_netem(status, netem):
    cmd = ''
    for iface in s.IFACE_ROUTER:
        cmd += "tc qdisc " + status + " dev " + iface + " root netem " + netem + " ; "
    return router_shell(cmd)

def enable_netem(netem):
    return manage_netem('add', netem)

def enable_netem_loss(value):
    return enable_netem(loss_cmd(str(value)))

def enable_netem_delay(value):
    return enable_netem(delay_cmd(str(value)))

def enable_netem_loss_delay(loss, delay):
    return enable_netem(loss_cmd(str(value)) + delay_cmd(str(value)))

def change_netem(netem):
    return manage_netem('change', netem)

def change_netem_loss(value):
    return change_netem(loss_cmd(str(value)))

def change_netem_delay(value):
    return change_netem(delay_cmd(str(value)))

def change_netem_loss_delay(loss, delay):
    return change_netem(loss_cmd(str(value)) + delay_cmd(str(value)))

def disable_netem():
    cmd = ''
    for iface in s.IFACE_ROUTER:
        cmd += "tc qdisc delete dev " + iface + " root ; "
    return router_shell(cmd)
