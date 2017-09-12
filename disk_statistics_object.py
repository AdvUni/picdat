"""
Contains the class DiskStatsObject
"""
import data_collector_util
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

    def __init__(self):
        self.statit_counter = 0
        self.statit_timestamps = []

        self.inside_statit_block = False
        self.inside_disk_stats_block = False

        self.table = Table()

    def check_statit_begin(self, line):
        if '---- statit ---' in line:
            self.statit_counter += 1
            self.inside_statit_block = True
            return True

    def process_disc_stats(self, line):
        line_split = line.split()
        if self.inside_disk_stats_block:
            if line == '':
                self.inside_statit_block = False
                self.inside_disk_stats_block = False
                return

            if len(line_split) == 1:
                return

            disk = line_split[0]
            ut_percent = line_split[1]

            self.table.insert(self.statit_counter, disk, ut_percent)

        else:
            if len(self.statit_timestamps) < self.statit_counter:
                if 'Begin: ' in line:
                    self.statit_timestamps.append(data_collector_util.build_date(line.split(' ',
                                                                                            1)[1]))
                return
            if line_split[0] == 'disk':
                self.inside_disk_stats_block = True
