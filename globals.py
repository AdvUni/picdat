"""
This module holds some variables, which are used in a global context. As they might change at 
runtime, they're not constant. These variables are meant to be set once during processing one 
PerfStat file and reset between two PerfStat files.
"""

__author__ = 'Marie Lohbeck'
__copyright__ = 'Copyright 2017, Advanced UniByte GmbH'


# license notice:
#
# This file is part of PicDat.
# PicDat is free software: you can redistribute it and/or modify it under the terms of the GNU
# General Public (at your option) any later version.
#
# PicDat is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without
# even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with PicDat. If not,
# see <http://www.gnu.org/licenses/>.

# PerfStat output might be somewhat inconsistent in dealing with timezones. Therefore,
# PicDat wants to convert all time information into local time. As local timezone, it takes the
# first timezone it finds in the PerfStat file.
localtimezone = None


def reset():
    """
    This function resets all global variables from this file back to None.
    :return: None
    """
    global localtimezone
    localtimezone = None