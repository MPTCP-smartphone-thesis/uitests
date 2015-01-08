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

if os.path.isfile('launch_tests_conf.py'):
    from launch_tests_conf import *

# Out in another dir
OUTPUT_DIR = '~/Thesis/TCPDump_bad_conditions'

# Tests both4 then with some losses or delays
NETWORK_TESTS = 'both4 both4TCL2p both4TCL5p both4TCL10p both4TCL15p both4TCL20p both4TCD5m both4TCD10m both4TCD25m both4TCD50m both4TCD100m'

# Tests with ShadowSocks
WITH_SSH_TUNNEL = False
WITH_SHADOWSOCKS = True

# Tests without MPTCP (to see the diff) and FullMesh
# (with the default path manager, we will not see the differences:
#  it will use only one IFace, the same as used without MPTCP)
WITH_TCP = True
WITH_MPTCP = False
WITH_FULLMESH = True

if os.path.isfile('launch_tests_conf_bad_conditions_custom.py'):
    from launch_tests_conf_bad_conditions_custom import *
