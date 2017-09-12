"""
Contains the class DiskStatsObject
"""
import util
from table import Table

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


class DiskStatsObject:
    """
    This object type is responsible for holding several information about statit blocks.
    in PerfStat output. It's a centralization of headers and values for the disk statistic charts.
    Further, it contains all other information necessary to read headers and values from a
    PerfStat file.
    """
    def __init__(self):
        self.statit_counter = 0
        self.statit_timestamps = []

        self.inside_statit_block = False
        self.inside_disk_stats_block = False

        self.table = Table()
        self.disk_names = set()

    def check_statit_begin(self, line):
        """
        This function looks, whether a line from a PerfStat output marks the beginning of a
        statit block. If so, it increments the statit_counter and sets the inside_statit_block
        boolean to true.
        :param line: A line from a PerfStat file as String.
        :return: True, if the line contains a statit beginning marker and False otherwise.
        """
        if '---- statit ---' in line:
            self.statit_counter += 1
            self.inside_statit_block = True
            return True

    def process_disc_stats(self, line):
        """
        Collects all relevant information from a line in a statit block. There are two
        possibilities: Either the relevant part of the statit block - the part under 'Disk
        statistics' - already began or it didn't. In case it did, the function collects the value
        and the disk from the line into the object's table. It also watches for the end of this
        block. Otherwise, it watches for the statit timestamp respectively for the 'Disk
        statistics' part's begin.
        :param line: A line from a PerfStat file as String.
        :return: None.
        """
        line_split = line.split()
        if self.inside_disk_stats_block:
            if len(line_split) == 0:
                self.inside_statit_block = False
                self.inside_disk_stats_block = False
                return

            if len(line_split) == 1:
                return

            disk = line_split[0]
            ut_percent = line_split[1]

            self.disk_names.add(disk)
            self.table.insert(self.statit_counter, disk, ut_percent)

        else:
            if len(line_split) == 0:
                return
            if len(self.statit_timestamps) < self.statit_counter:
                if 'Begin: ' in line:
                    self.statit_timestamps.append(util.build_date(line.split(' ', 1)[1]))
                return
            if line_split[0] == 'disk':
                self.inside_disk_stats_block = True

    def flatten_table(self):
        return self.table.get_rows(self.disk_names, self.statit_timestamps)
