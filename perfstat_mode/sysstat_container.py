"""
Contains the class SysstatContainer. This class is responsible for processing certain kind
of search keys. The sysstat keys are about some blocks in the PerfStat called something like
'sysstat_x_1sec'. These blocks are expected to appear once per PerfStat iteration. The
blocks are built like tables with a header and many rows of values. The time gap between two rows of
values is exactly one second - this is why the block has its name. Different columns in PerfStat's
sysstat table usually refer to different units. PicDat is interested in only some of the columns.
They are specified in the sysstat-keys constants. The search keys are subdivided into three lists,
each one belonging to a specific unit. PicDat is going to create exactly three csv tables and three
charts about the sysstat blocks.
"""
import re

import logging

from perfstat_mode import constants
from perfstat_mode import util

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


# These search keys will match many times inside sysstat_x_1sec blocks. They all belong to unit
# %. Data collected about these search keys will be shown in one chart together.
# About the data structure: A list of tuples. Each tuple contains the name of a measurement in
# the first place and an additional identifier, which appears in the second sysstat header line,
# in the second place.
SYSSTAT_PERCENT_KEYS = [('CPU', ' '), ('Disk', 'util'), ('HDD', 'util'), ('SSD', 'util')]
SYSSTAT_PERCENT_UNIT = '%'

# These search keys will match many times inside sysstat_x_1sec blocks. They all belong to unit
# kB/s, but PicDat will convert the values to MB/s for better readability. Data collected about
# these search keys will be shown in one chart together.
# About the data structure: A list of tuples. Each tuple contains the name of a measurement in
# the first place. In the second place is another tuple, containing two parameters, e.g. 'read'
# and 'write'.
SYSSTAT_MBS_KEYS = [('Net', ('in', 'out')), ('FCP', ('in', 'out')), ('Disk', ('read', 'write')),
                    ('HDD', ('read', 'write')), ('SSD', ('read', 'write'))]
SYSSTAT_MBS_UNIT = 'MB/s'

# These search keys will match many times inside sysstat_x_1sec blocks. They values for them
# haven't any unit; they're absolute. Data collected about this search keys will be shown in one
# chart together.
SYSSTAT_IOPS_KEYS = ['NFS', 'CIFS', 'FCP', 'iSCSI']
SYSSTAT_IOPS_UNIT = ' '

SYSSTAT_CHART_TITLE = 'sysstat_1sec'


class SysstatContainer:
    """
    This class is responsible for holding several information about sysstat_x_1sec blocks
    in PerfStat output. It's a container for headers and values for sysstat charts. Further,
    it contains all other information necessary to read headers and values from a PerfStat file.
    """

    def __init__(self):

        # boolean, whether program is currently reading in a sysstat_x_1sec block:
        self.inside_sysstat_block = False

        # boolean, which turns to False, once the program saved headers for the sysstat_x_1sec block
        # (Header should be equal for each block):
        self.sysstat_header_needed = True

        # the recent time:
        self.recent_timestamp = None

        # lists to hold the headers for the three sysstat-charts:
        self.percent_headers = []
        self.mbs_headers = []
        self.iops_headers = []

        # lists to hold the column indices being interesting for the three sysstat-charts:
        self.percent_indices = []
        self.mbs_indices = []
        self.iops_indices = []

        # lists to hold the values for the three sysstat-charts:
        self.percent_values = []
        self.mbs_values = []
        self.iops_values = []

        # to analyse a sysstat header, it is necessary to look at two lines at once. But because
        # the program reads line by line, this variable is for buffering the first header line:
        self.buffered_header = None

    def found_sysstat_1sec_begin(self, line):
        """
        Looks, whether a String marks the beginning of a sysstat_x_1sec respectively sysstat_1sec
        section and in case sets the container's variable inside_sysstat_block.
        :param line: A string from a PerfStat output file which should be searched
        :return: True, if the line marks the beginning of a sysstat_x_1sec or sysstat_1sec section,
        or False otherwise.
        """
        if 'sysstat_x_1sec' in line or '-= sysstat_1sec' in line:
            self.inside_sysstat_block = True
            return True

        return False

    def collect_sysstat_timestamp(self, sysstat_timestamp_line, iteration_timestamp):
        """
        Extract a date from a PerfStat output line which contains the time, a sysstat_x_1sec block
        begins. Saves the date to the container's variable recent_timestamp.
        :param sysstat_timestamp_line: a string like
        PERFSTAT_EPOCH: 0000000000 [Mon Jan 01 00:00:00 GMT 2000]
        :param iteration_timestamp: The the recent iteration's beginning timestamp. It would be
        used as sysstat beginning timestamp, in case that there is no timestamp available in
        sysstat_timestamp_line on account of a PerfStat bug.
        :return: None
        """
        try:
            # extract time stamp from cdot perfstat:
            self.recent_timestamp = util.build_date(
                sysstat_timestamp_line.split('[')[1].replace(']', ''))

        except IndexError:
            try:
                # extract time stamp from 7-mode perfstat:
                self.recent_timestamp = util.build_date(
                    sysstat_timestamp_line.replace('Begin: ', ''))
            except (KeyError, IndexError, ValueError):
                logging.warning(
                    'PerfStat bug in sysstat block. Could not read any timestamp from line: '
                    '\'%s\' PicDat is using the timestamp from the iteration\'s beginning '
                    'instead. This timestamp is: \'%s\' Note that this may lead to '
                    'falsifications in charts!', sysstat_timestamp_line, iteration_timestamp)
                self.recent_timestamp = iteration_timestamp

        except (KeyError, ValueError):
            logging.warning(
                'PerfStat bug in sysstat block. Could not read any timestamp from line: '
                '\'%s\' PicDat is using the timestamp from the iteration\'s beginning '
                'instead. This timestamp is: \'%s\' Note that this may lead to '
                'falsifications in charts!', sysstat_timestamp_line, iteration_timestamp)
            self.recent_timestamp = iteration_timestamp

    def increment_time(self):
        """
        Increases the container's datetime variable 'recent_timestamp' about one second.
        :return: None
        """
        self.recent_timestamp += constants.ONE_SECOND

    def add_empty_lines(self):
        """
        Adds an empty data line to each value list inside this container. This is for interrupting
        the templates graph lines in resulting charts. Therefore, this function should be called
        between iterations.
        :return: None
        """
        for value_list in [self.percent_values, self.mbs_values, self.iops_values]:
            empty_line = util.empty_line(value_list)
            if empty_line is not None:
                value_list.append(empty_line)

    def process_sysstat_keys(self, value_line):
        """
        This function collects all relevant information from a line in a sysstat_x_1sec block. In
        case, the line doesn't contain values, but a sub header, the function ignores it.
        Otherwise, the function is going to append one sublist onto each of the own value lists.
        Therefore, it uses the container's index lists to find the right value places inside the
        sysstat block.
        :param value_line: A String which is a line from a sysstat_x_1sec block
        :return: True, if value_line really contained values and False, if it just was a sub header.
        """
        line_split = value_line.split()
        if len(line_split) == 0:
            return

        # check, whether line really contains data and not just a sub header
        if str.isdigit(line_split[0].strip('%')):
            # add values specified in percent_indices to percent_values
            self.percent_values.append([str(self.recent_timestamp)] + [line_split[index].strip(
                '%') for index in self.percent_indices])
            # add values specified in mbs_indices to mbs_values and convert them to MB/s instead of
            # kB/s. Notice, that this needs to be conform to the constant SYSSTAT_MBS_UNIT!
            self.mbs_values.append(
                [str(self.recent_timestamp)] +
                [str(round(int(line_split[index]) / 1000)) for index in self.mbs_indices])

            self.iops_values.append([str(self.recent_timestamp)] + [line_split[index] for index in
                                                                    self.iops_indices])
            self.increment_time()

    def process_sysstat_header(self, first_header_line, second_header_line):
        """
        Searches the header of a sysstat_x_1sec block, which is usually split over two lines,
        for the requested columns. Saves the headers matching a search_key to the container's
        header lists. Also saves the column numbers belonging to those headers to the
        container's index lists.
        :param first_header_line: The first line of a sysstat_x_1sec header
        :param second_header_line: The second line of a sysstat_x_1sec header
        :return: None
        """
        self.sysstat_header_needed = False

        # Split the first line into single words and save them to header_line_split.
        # Simultaneously, memorize the line indices, at which the words end, into endpoints.
        header_line_split, endpoints = zip(
            *[(m.group(0), m.end()) for m in re.finditer(r'\S+', first_header_line)])

        # iterate over header_line_split:
        for index in range(len(header_line_split)):

            # iterate over the sysstat search keys, which belong to the unit %:
            for search_key in SYSSTAT_PERCENT_KEYS:
                if util.check_column_header(header_line_split[index], endpoints[index],
                                            second_header_line, search_key[0], search_key[1]):
                    if search_key[1] == ' ':
                        self.percent_headers.append(search_key[0])
                    else:
                        self.percent_headers.append(
                            str(search_key[0]) + '_' + str(search_key[1]))
                    self.percent_indices.append(index)

            # iterate over the sysstat search keys, which belong to the unit MB/s:
            for search_key in SYSSTAT_MBS_KEYS:
                if util.check_column_header(header_line_split[index], endpoints[index],
                                            second_header_line, search_key[0], search_key[1][0]):
                    self.mbs_headers.append(str(search_key[0]) + '_' + str(search_key[1][0]))
                    self.mbs_indices.append(index)
                    # Measurements for the MB/s chart always come with two parameters, e.g. 'read'
                    # and 'write'. There is no way to read them from the header lines separately,
                    # so we find them and add their columns to header_list and index_list at once
                    self.mbs_headers.append(str(search_key[0]) + '_' + str(search_key[1][1]))
                    self.mbs_indices.append(index + 1)

            # iterate over the sysstat search keys, which belong to no unit:
            for search_key in SYSSTAT_IOPS_KEYS:
                if util.check_column_header(header_line_split[index], endpoints[index],
                                            second_header_line, search_key, ' '):
                    self.iops_headers.append(search_key)
                    self.iops_indices.append(index)

        logging.debug('sysstat_percent_headers: ' + str(self.percent_headers))
        logging.debug('sysstat_mbs_headers: ' + str(self.mbs_headers))
        logging.debug('sysstat_iops_headers: ' + str(self.iops_headers))

    def process_sysstat_block(self, line):
        """
        Collects all relevant information from a sysstat_x_1sec block. If the header isn't
        analysed yet, it will do this. Otherwise it only takes care of the values. Further,
        it recognizes if the sysstat block is over.
        :param line: A line from a PerfStat file as String.
        :return: None.
        """
        # '--' marks, that a sysstat_x_1sec block ends.
        if line.startswith('--'):
            self.inside_sysstat_block = False
            self.buffered_header = None
        elif line.startswith('Command got killed'):
            self.inside_sysstat_block = False
            self.buffered_header = None
            logging.info('sysstat data is not available! Instead of data, found following line '
                         'under sysstat header: "%s" Charts might be empty.', line.strip())
        elif self.sysstat_header_needed:
            if self.buffered_header is None:
                if len(line.strip()) != 0:
                    self.buffered_header = line
            else:
                self.process_sysstat_header(self.buffered_header, line)
                self.buffered_header = None
        else:
            self.process_sysstat_keys(line)

    def rework_sysstat_data(self):
        """
        Simplifies data structures: Adds 'time' Strings to the header lists, then sticks headers
        and values for each table together, then sticks all tables together.
        :return: All sysstat tables in a nested list.
        """
        for value_list in [self.percent_values, self.mbs_values, self.iops_values]:
            try:
                while value_list[-1][0] == ' ':
                    del value_list[-1]
            except IndexError:
                pass

        self.percent_headers.insert(0, 'time')
        self.mbs_headers.insert(0, 'time')
        self.iops_headers.insert(0, 'time')

        tables = []

        # check for all tables whether they are empty before returning them
        if self.percent_values:
            tables += [[self.percent_headers] + self.percent_values]
        if self.mbs_values:
            tables += [[self.mbs_headers] + self.mbs_values]
        if self.iops_values:
            tables += [[self.iops_headers] + self.iops_values]

        return tables

    def get_labels(self):
        """
        This method provides meta information for the data found about sysstat charts.
        Those are the chart identifiers (tuple of two strings, unique for each chart, used for
        chart titles, file names etc), units, and a boolean for each chart, which says, whether
        the chart is a histogram (histograms are visualized differently, but sysstat results are
        not meant to be histograms in general, so this is always False for this class).
        :return: a triple of the lists identifiers, units and is_histo, containing the mentioned
        information
        """
        identifiers = []
        units = []
        is_histo = []

        # check for all tables whether they are empty before returning their labels
        if self.percent_values:
            identifiers.append((SYSSTAT_CHART_TITLE, 'percent'))
            units.append(SYSSTAT_PERCENT_UNIT)
            is_histo.append(False)
        if self.mbs_values:
            identifiers.append((SYSSTAT_CHART_TITLE, 'MBs'))
            units.append(SYSSTAT_MBS_UNIT)
            is_histo.append(False)
        if self.iops_values:
            identifiers.append((SYSSTAT_CHART_TITLE, 'IOPS'))
            units.append(SYSSTAT_IOPS_UNIT)
            is_histo.append(False)

        return identifiers, units, is_histo
