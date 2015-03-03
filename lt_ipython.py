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

import importlib
from IPython import embed

# force to be in the right dir
import os
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT_DIR)

import lt_globals as g
g.init()

import lt_settings as s # config
s.init()

import lt_device as dev
import lt_network as net

from lt_tcp import TCP
from lt_utils import *

def reload(module=None):
    if module:
        importlib.reload(module)
    else:
        importlib.reload(g)
        importlib.reload(s)
        importlib.reload(dev)
        importlib.reload(net)
        # importlib.reload(TCP)

embed()
