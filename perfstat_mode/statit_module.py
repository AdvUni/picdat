"""
Contains the class StatitClass. This class is responsible for processing a certain request
type. The statit-requests are about some blocks in the PerfStat called something like 'statit'.
These blocks may appear several times in a PerfStat iteration. PicDat is interested in a special
subsection of the statit block called 'Disk Statistics'. This subsections holds a table of
information about all disks of the device the PerfStat is about. PicDat only looks for the first
two columns of this table: The first one contains the disk names and the second one a related
number called 'ut%'. PicDat is going to create exactly one csv table and one chart about the
statit blocks.
"""
import logging

from perfstat_mode import constants
from perfstat_mode import util
from general.table import Table

__author__ = 'Marie Lohbeck'
__copyright__ = 'Copyright 2018, Advanced UniByte GmbH'

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

STATIT_DISK_STAT_UNIT = '%'
STATIT_CHART_TITLE = 'statit%sdisk_statistics'


class StatitClass:
    """
    This object type is responsible for holding several information about statit blocks.
    in PerfStat output. It's a centralization of headers and values for the disk statistic charts.
    Further, it contains all other information necessary to read headers and values from a
    PerfStat file.
    """

    def __init__(self, sort_columns_by_name):
        """
        Constructor for StatitClass.
        :param sort_columns_by_name: Graph lines in statit charts might become pretty many.
        Per default, PicDat sorts the legend entries by relevance, means the graph with the
        highest values in sum is displayed at the top of the legend. If you rather would sort
        them alphabetically, this boolean should be true.
        """

        # An integer tracking the number of --- statit --- lines, PicDat read in the PerfStat.#
        # As the statit timestamp is always some lines beneath, this counter is used to check
        # whether PicDat needs to look for a new timestamp:
        self.statit_counter = 0
        # A list of all statit timestamps:
        self.statit_timestamps = []

        # A boolean, which says, whether program is recently inside a statit block (but not
        # necessarily inside a disk statistic block!):
        self.inside_statit_block = False
        # A boolean, which says, whether program is recently inside a disk statistic block (a
        # block inside the statit block):
        self.inside_disk_stats_block = False

        # A variable of type 'Table', should collect all values from disk statistic blocks:
        self.table = Table()

        # This variable should save the self.table content in a flattened form:
        self.flat_table = None

        # If PerfStat broke a line, this variable should buffer the snippet:
        self.line_buffer = None

        self.sort_columns_by_name = sort_columns_by_name

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
        else:
            return False

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
            if len(line_split) == 0 \
                    or line == 'Aggregate statistics:' \
                    or line == 'Spares and other disks:':
                self.inside_statit_block = False
                self.inside_disk_stats_block = False
                self.line_buffer = None
                return

            # don't care about sub headers:
            if len(line_split) == 1 and line.startswith('/') and line.endswith(':'):
                self.line_buffer = None
                return

            # In Disk Statistics blocks, PerfStat sometimes seems to break some lines out of
            # nowhere. Therefore, the program buffers line snippets and sticks them together at
            # next method call.
            if len(line_split) < constants.STATIT_COLUMNS:
                if self.line_buffer is None:
                    self.line_buffer = line
                    logging.debug('buffered statit line snippet: %s', line)
                    return
                else:
                    line_split = self.line_buffer.split() + line_split
                    logging.debug('joined statit line: %s', line_split)

            disk = line_split[0]
            ut_percent = line_split[1]

            self.table.insert(self.statit_timestamps[-1], disk, ut_percent)

            self.line_buffer = None

        else:
            if len(line_split) == 0:
                return
            if len(self.statit_timestamps) < self.statit_counter:
                if 'Begin: ' in line:
                    try:
                        self.statit_timestamps.append(util.build_date(line.split(' ', 1)[1]))
                    except (KeyError, IndexError, ValueError):

                        if not self.statit_timestamps:
                            alternative_timestamp = constants.DEFAULT_TIMESTAMP

                            logging.warning(
                                'PerfStat bug in statit block. Could not read any timestamp '
                                'from line: \'%s\' This should have been the very first statit '
                                'timestamp of this document. PicDat is using default timestamp '
                                'instead. This timestamp is: \'%s\'. Note that this may lead to '
                                'falsifications in charts!', line.strip(), alternative_timestamp)

                        else:
                            alternative_timestamp = self.statit_timestamps[-1]
                            logging.warning(
                                'PerfStat bug in statit block. Could not read any timestamp '
                                'from line: \'%s\' PicDat is using the timestamp from the last '
                                'statit block instead. This timestamp is: \'%s\'. Note that this '
                                'may lead to falsifications in charts!',
                                line.strip(), alternative_timestamp)

                        self.statit_timestamps.append(alternative_timestamp)
                return
            if line_split[0] == 'disk':
                self.inside_disk_stats_block = True

    def rework_statit_data(self, iteration_timestamps):
        """
        Simplifies statit data: Flattens the table data structure. Also inserts empty data lines
        to separate iterations in resulting charts from each other.
        :param iteration_timestamps: A list of datetime objects, marking the ends of all
        iterations in one PerfStat file. They are needed to insert the empty lines at the right
        places.
        :return: The flattened table in a list.
        """
        if self.table.is_empty():
            return []

        self.flat_table = self.table.flatten('time', self.sort_columns_by_name)
        self.add_empty_lines(iteration_timestamps)

        return [self.flat_table]

    def add_empty_lines(self, iteration_end_timestamps):
        """
        Inserts empty data lines into the flat_values list retroactively. The empty lines are
        inserted between two rows belonging to different iterations. This is for interrupting the
        templates graph lines between iterations in resulting charts.
        :param iteration_end_timestamps: A list of datetime objects, marking the ends of all
        iterations in one PerfStat file.
        :return: None
        """
        iter_iterations = iter(iteration_end_timestamps)
        next_iteration = next(iter_iterations)
        counter = 0
        try:
            for statit in self.statit_timestamps:
                logging.debug('statit timestamp %s vs. iteration timestamp %s', statit,
                              next_iteration)
                if next_iteration < statit:
                    if counter > 0:
                        self.flat_table.insert(counter + 1, util.empty_line(self.flat_table[1:]))
                        next_iteration = next(iter_iterations)
                    counter += 1
                counter += 1
        except StopIteration:
            pass

    def get_units(self):
        if self.table.is_empty():
            return []
        return [STATIT_DISK_STAT_UNIT]

    def get_request_strings(self, delimiter):
        if self.table.is_empty():
            return []
        return [STATIT_CHART_TITLE % delimiter]

    def get_x_labels(self):
        if self.table.is_empty():
            return []
        return ['time']

    def get_barchart_booleans(self):
        if self.table.is_empty():
            return []
        return ['false']

    def get_titles(self):
        return self.get_request_strings(': ')

    def get_object_ids(self):
        return self.get_request_strings('_')
