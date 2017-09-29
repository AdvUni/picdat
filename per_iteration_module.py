"""
Contains the class PerIterationClass. This class is responsible for processing a certain request
type. Per-iteration requests are looking for values about several aspects of different object types
which have several instances. There are no specific blocks in the PerfStat in which those values
appears, but for each triple of an object type, one specific instance and a certain aspect,
there is expected exactly one value per iteration. PicDat collects these values and is going to
create one csv table together with one dygraph chart for each aspect about each object type.
Therefore, one chart will display several instances.
"""
import logging

import constants
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


# These search keys will match (at most) once in each iteration. They are represented as tuples
# of an aspect key word and the corresponding unit. Data collected about one tuple will be shown
# in exactly one chart.
PER_ITERATION_AGGREGATE_REQUESTS = [('total_transfers', '/s')]
PER_ITERATION_PROCESSOR_REQUESTS = [('processor_busy', '%')]
PER_ITERATION_VOLUME_REQUESTS = [('total_ops', '/s'), ('avg_latency', 'us'), ('read_data', 'b/s')]
PER_ITERATION_LUN_REQUESTS = [('total_ops', '/s'), ('avg_latency', 'ms'), ('read_data', 'b/s')]
# This search request is special: It is not searching for one value per lun per iteration,
# but exactly eight values for each lun, representing the different buckets. Because the PerfStat
# is expected to have eight values per lun per iteration, PicDat is going to show only the last
# collected value.
PER_ITERATION_LUN_ALIGN_REQUEST = ('read_align_histo', '%')


def get_iteration_timestamp(iteration_timestamp_line, last_timestamp):
    """
    Extract a date from a PerfStat output line which marks an iteration's beginning or ending
    :param iteration_timestamp_line: a string like
    =-=-=-=-=-= BEGIN Iteration 1  =-=-=-=-=-= Mon Jan 01 00:00:00 GMT 2000
    :param last_timestamp: The last iteration timestamp, the program has collected. It would be
    used as recent timestamp, in case that there is no timestamp available in
    iteration_timestamp_line on account of a PerfStat bug.
    :return: a datetime object which contains the input's time information
    """

    try:
        return util.build_date(iteration_timestamp_line.split('=-=-=-=-=-=')[2])
    except (KeyError, IndexError, ValueError):

        if last_timestamp is None:
            last_timestamp = constants.DEFAULT_TIMESTAMP
            logging.warning(
                'PerfStat bug. Could not read any timestamp from line: \'%s\' This should have '
                'been the very first iteration timestamp. PicDat is using default timestamp '
                'instead. This timestamp is: \'%s\'. Note that this may lead to falsifications in '
                'charts!', iteration_timestamp_line, str(last_timestamp))
        else:
            logging.warning(
                'PerfStat bug. Could not read any timestamp from line: \'%s\' PicDat is using '
                'last collected iteration timestamp (timestamp from a \'BEGIN Iteration\' or '
                '\'END Iteration\' line) instead. This timestamp is: \'%s\'. Note that this may '
                'lead to falsifications in charts!', iteration_timestamp_line, str(last_timestamp))
        return last_timestamp


class PerIterationClass:
    """
    This object type is responsible for holding the information collected in one PerfStat file
    about the per_iteration_requests. It's a centralization of headers and values for per_iteration
    charts. Further, it contains some values needed to visualize the data correctly.
    """

    def __init__(self, sort_columns_by_name):
        """
        Constructor for PerIterationClass.
        :param sort_columns_by_name: Graph lines in per-iteration charts might become pretty many.
        Per default, PicDat sorts the legend entries by relevance, means the graph with the
        highest values in sum is displayed at the top of the legend. If you rather would sort
        them alphabetically, this boolean should be true.
        """

        # Several lists of type 'Table', one for each of the request lists. They'll collect all
        # per-iteration values from a  PerfStat output file, grouped by iteration and instance:
        self.aggregate_tables = []
        self.processor_tables = []
        self.volume_tables = []
        self.lun_tables = []
        self.lun_alaign_table = Table()

        # A boolean, whether lun values appeared in the PerfStat at all:
        self.luns_available = False

        # A dictionary translating the LUNs IDs into their paths:
        self.lun_path_dict = {}

        # To translate lun IDs into their paths, it needs to read more than one line. Following
        # variable is for buffering a lun path until the corresponding ID is found:
        self.lun_buffer = None

        self.sort_columns_by_name = sort_columns_by_name

    @staticmethod
    def process_object_type(iteration_timestamp, requests, tables, line_split):
        """
        Processes one of the per-iteration request types.
        :param iteration_timestamp: The timestamp of the PerfStat iteration, the line is from.
        :param requests: One of the module's per-iteration request lists. Method would be search
        for them.
        :param tables: One of the object's table list. Should fit to the requests. If method
        found a value, it will write it into this table.
        :param line_split: The words from a PerfStat line as list.
        :return: None.
        """
        request_index = 0
        for (aspect, unit) in requests:
            if line_split[2] == aspect:
                instance = line_split[1]
                value = line_split[3][:-len(unit)]

                # we want to convert b/s into MB/s, so if the unit is b/s, lower the
                # value about factor 10^6. Pay attention, that this conversion
                # implies an adaption in the get_units method, where the unit also should be
                # changed to MB/s!
                if unit == 'b/s':
                    value = str(round(int(value) / 1000000))

                util.tablelist_insertion(tables, request_index, iteration_timestamp, instance,
                                         value)
                logging.debug('Found value about %s, %s: %s - %s%s', line_split[0], aspect,
                              instance, value, unit)
                return
            request_index += 1

    def process_per_iteration_requests(self, line, iteration_timestamp):
        """
        Searches a String for all per_iteration_requests from main. In case it finds something,
        it writes the results into the correct place in table_values. During the first iteration it
        collects the instance names of all requested object types as well and writes them into
        table_headers.
        :param line: A string from a PerfStat output file which should be searched
        :param iteration_timestamp: The timestamp of the PerfStat iteration, the line is from.
        :return: None
        """
        if 'LUN ' in line:
            self.map_lun_path(line)
            return

        line_split = line.split(':')

        if len(line_split) < 4:
            return

        object_type = line_split[0]

        if object_type == 'aggregate':
            self.process_object_type(iteration_timestamp, PER_ITERATION_AGGREGATE_REQUESTS,
                                     self.aggregate_tables, line_split)
            return
        if object_type == 'processor':
            self.process_object_type(iteration_timestamp, PER_ITERATION_PROCESSOR_REQUESTS,
                                     self.processor_tables, line_split)
            return
        if object_type == 'volume':
            self.process_object_type(iteration_timestamp, PER_ITERATION_VOLUME_REQUESTS,
                                     self.volume_tables, line_split)
            return
        if object_type == 'lun':
            self.luns_available = True

            # lun: ... :read_align_histo.x values shouldn't be visualized related on
            # timestamps, but on the value x in range 0-8. So, they need to be handled
            # specially:
            align_aspect, align_unit = PER_ITERATION_LUN_ALIGN_REQUEST
            if align_aspect in line_split[2]:
                instance = line_split[1]
                number = int(line_split[2][-1])
                value = line_split[3][:-len(align_unit)]

                self.lun_alaign_table.insert(number, instance, value)
                logging.debug('Found value about %s, %s(%i): %s - %s%s', object_type,
                              align_aspect, number, instance, value, align_unit)
            else:
                self.process_object_type(iteration_timestamp, PER_ITERATION_LUN_REQUESTS,
                                         self.lun_tables, line_split)
            return

    def map_lun_path(self, line):
        """
        Builds a dictionary to translate each LUN's uuid into it's path for better readability.
        Looks for a 'LUN Path' or a 'LUN UUID' keyword. In case it finds a path, it buffers the
        path name. In case a uuid is found, it writes the uuid in the lun_path_dict together with
        the lun path name last buffered.
        :param line: A string from a PerfStat output file which should be searched
        :return: None
        """
        if 'LUN Path: ' in line:
            try:
                self.lun_buffer = str(line.split()[2])
            except IndexError:
                logging.warning('Expected a LUN path in line, but didn\'t found any: \'%s\'', line)
        elif 'LUN UUID: ' in line:
            try:
                lun_uuid = line.split()[2]
                if self.lun_buffer is None:
                    logging.info('Found LUN uuid \'%s\' but no corresponding path translation.',
                                 lun_uuid)
                else:
                    logging.debug('Found translation for LUN %s: \'%s\'', lun_uuid, self.lun_buffer)
                    self.lun_path_dict[lun_uuid] = self.lun_buffer
                    self.lun_buffer = None
            except IndexError:
                logging.warning('Expected a LUN uuid in line, but didn\'t found any: \'%s\'', line)

    def rework_per_iteration_data(self):
        """
        Simplifies data structures: Flattens tables from the table lists and sticks them all
        together. Further, replaces the ID of each LUN in the headers with their paths for better
        readability.
        :return: All flattened tables in a list.
        """
        # replace lun's IDs in headers through their path names
        self.replace_lun_ids()

        all_tables = self.aggregate_tables + self.processor_tables + self.volume_tables
        if self.luns_available:
            all_tables += self.lun_tables
            all_tables.append(self.lun_alaign_table)
        else:
            logging.info('Seems like PerfStat doesn\'t contain any information about LUNs.')

        x_labels = self.get_x_labels()

        flat_tables = []
        for table in range(len(all_tables)):
            flat_tables.append(
                all_tables[table].flatten(x_labels[table], self.sort_columns_by_name))

        return flat_tables

    def replace_lun_ids(self):
        """
        All values in PerfStat corresponding to LUNs are given in relation to their UUID, not their
        name or path. To make the resulting charts more readable, this function replaces their IDs
        with the paths.
        :return: None.
        """
        if not self.luns_available:
            return

        for table in self.lun_tables + [self.lun_alaign_table]:
            for outer_key, inner_dict in table.outer_dict.items():
                replace_dict = {}
                for uuid in inner_dict:
                    if uuid in self.lun_path_dict:
                        replace_dict[self.lun_path_dict[uuid]] = inner_dict[uuid]
                    else:
                        logging.info('Could not find path for LUN ID \'%s\'! LUN will be displayed '
                                     'with ID.', uuid)
                table.outer_dict[outer_key] = replace_dict

    def get_units(self):
        requests = PER_ITERATION_AGGREGATE_REQUESTS + PER_ITERATION_PROCESSOR_REQUESTS + \
                   PER_ITERATION_VOLUME_REQUESTS
        if self.luns_available:
            requests += PER_ITERATION_LUN_REQUESTS
            requests.append(PER_ITERATION_LUN_ALIGN_REQUEST)

        all_units = []
        for (_, unit) in requests:
            # we want to convert b/s into MB/s, so if the unit is b/s, display it as MB/s.
            # Pay attention, that this rename needs to be compatible with the
            # process_object_type method, where the affected values should be reduced by the
            # factor 10^6!
            if unit == 'b/s':
                all_units.append('MB/s')
            else:
                all_units.append(unit)
        return all_units

    def get_request_strings(self, delimiter):
        title_list = []

        title_list += ['aggregate' + delimiter + aspect for (aspect, _) in
                       PER_ITERATION_AGGREGATE_REQUESTS]
        title_list += ['processor' + delimiter + aspect for (aspect, _) in
                       PER_ITERATION_PROCESSOR_REQUESTS]
        title_list += ['volume' + delimiter + aspect for (aspect, _) in
                       PER_ITERATION_VOLUME_REQUESTS]

        if self.luns_available:
            title_list += ['lun' + delimiter + aspect for (aspect, _) in
                           PER_ITERATION_LUN_REQUESTS]
            title_list.append('lun' + delimiter + PER_ITERATION_LUN_ALIGN_REQUEST[0])

        return title_list

    def get_x_labels(self):

        x_lable_list = ['time' for _ in PER_ITERATION_AGGREGATE_REQUESTS +
                        PER_ITERATION_PROCESSOR_REQUESTS + PER_ITERATION_VOLUME_REQUESTS]

        if self.luns_available:
            x_lable_list += ['time' for _ in PER_ITERATION_LUN_REQUESTS]
            x_lable_list.append('bucket')

        return x_lable_list

    def get_barchart_booleans(self):

        barchart_list = ['false' for _ in PER_ITERATION_AGGREGATE_REQUESTS +
                         PER_ITERATION_PROCESSOR_REQUESTS + PER_ITERATION_VOLUME_REQUESTS]

        if self.luns_available:
            barchart_list += ['false' for _ in PER_ITERATION_LUN_REQUESTS]
            barchart_list.append('true')

        return barchart_list
