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

from enum import Enum

class TCP(Enum):

    TCP               = 'TCP'
    MPTCP             = 'MPTCP'
    MPTCP_FULLMESH    = 'MPTCP_FM'
    MPTCP_FULLMESH_RR = 'MPTCP_RR'
    MPTCP_BACKUP      = 'MPTCP_BK'
    MPTCP_NDIFFPORTS  = 'MPTCP_ND'

    def is_tcp(self):
        return self.value.startswith('TCP')

    def is_mptcp(self):
        return self.value.startswith('MPTCP')

    def is_mptcp_not_default(self):
        return self.value.startswith('MPTCP_')

    def __str__(self):
        return self.value
