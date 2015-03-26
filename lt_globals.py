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

def init():
    global LAST_UPTIME, TEST_NO, NB_TESTS, SAVE_DIR, RMNET_IP
    LAST_UPTIME = ()
    TEST_NO = 0
    NB_TESTS = 0
    SAVE_DIR = 'TCPDump/test' # join(basedir(OUTPUT_DIR), time + git_rev) # unix mode!
    RMNET_IP = False
