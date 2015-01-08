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

import time
import sys

import lt_settings as s

# custom print
def my_print(msg, start=s.GREEN):
    print(start + "\n[" + time.strftime("%Y%m%d-%H%M%S") + "] " + str(msg) + "\n" + s.WHITE_STD)

def my_print_err(msg, start=s.RED):
    print(start + "\n[" + time.strftime("%Y%m%d-%H%M%S") + "]\t*** ERROR " + str(msg) + "\n" + s.WHITE_ERR, file=sys.stderr)
