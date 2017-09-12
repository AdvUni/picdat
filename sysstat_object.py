"""
Contains the class SysstatObject
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


class SysstatObject:
    """
    This object type is responsible for holding several information about sysstat_x_1sec blocks
    in PerfStat output. It's a centralization of headers and values for sysstat charts. Further,
    it contains all other information necessary to read headers and values from a PerfStat file.
    """
    def __init__(self):

        # boolean, whether program is currently reading in a sysstat_x_1sec block:
        self.inside_sysstat_block = False

        # boolean, which turns to False, once the program saved headers for the sysstat_x_1sec block
        # (Header should be equal for each block):
        self.sysstat_header_needed = True

        # lists to hold the headers for the both sysstat-charts:
        self.percent_headers = []
        self.mbs_headers = []
        self.iops_headers = []

        # lists to hold the column indices being interesting for the both sysstat-charts:
        self.percent_indices = []
        self.mbs_indices = []
        self.iops_indices = []

        # lists to hold the values for the both sysstat-charts:
        self.percent_values = []
        self.mbs_values = []
        self.iops_values = []

    def add_empty_lines(self):
        """
        Adds an empty data line to each value list inside this object. This is for interrupting the
        dygraphs graph lines in resulting charts. Therefore, this function should be called between
        iterations.
        :return: None
        """
        sysstat_value_lists = [self.percent_values, self.mbs_values, self.iops_values]

        for value_list in sysstat_value_lists:

            if value_list[0] is not None:
                columns = len(value_list[0])
                value_list.append([' ' for _ in range(columns + 1)])
