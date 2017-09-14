"""
Contains the class PerIterationObject.
"""
import util
from exceptions import InstanceNameNotFoundException
from requests import PER_ITERATION_REQUESTS
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


class PerIterationObject:
    """
    This object type is responsible for holding the information collected in one PerfStat file
    about the per_iteration_requests. It's a centralization of headers and values for per_iteration
    charts. Further, it contains some values needed to visualize the data correctly.
    """

    def __init__(self):

        # A list from type 'Table'. It collects all per-iteration values from a  PerfStat output
        # file, grouped by iteration and instance:
        self.tables = []

        # A List of Sets collecting all instance names (column names) occurring in one table:
        self.instance_names = []

        self.alaign_table = Table()
        self.alaign_instances = set()

        # A boolean, whether lun values appeared in the PerfStat at all:
        self.luns_available = False

        # A dictionary translating the LUNs IDs into their paths:
        self.lun_path_dict = {}

        # To translate lun IDs into their paths, it needs to read more than one line. Following
        # variable is for buffering a lun path until the corresponding ID is found:
        self.lun_buffer = None

        self.flat_headers = None
        self.flat_values = None

    def process_per_iteration_requests(self, line, recent_iteration):
        """
        Searches a String for all per_iteration_requests from main. In case it finds something,
        it writes the results into the correct place in table_values. During the first iteration it
        collects the instance names of all requested object types as well and writes them into
        table_headers.
        :param line: A string from a PerfStat output file which should be searched
        :param recent_iteration: An integer which says, in which perfStat iteration the function
        call happened
        :return: None
        """
        if 'LUN ' in line:
            self.map_lun_path(line)
            return

        request_index = 0
        line_split = line.split(':')

        if len(line_split) < 4:
            return

        for object_type in PER_ITERATION_REQUESTS:
            if line_split[0] == object_type:
                inner_tuples = PER_ITERATION_REQUESTS[object_type]

                for tuple_iterator in range(len(inner_tuples)):
                    aspect = inner_tuples[tuple_iterator][0]

                    # lun: ... :read_align_histo.x values shouldn't be visualized related on
                    # timestamps, but on the value x in range 0-8. So, they need to be handled
                    # specially:
                    if aspect == 'read_align_histo':
                        if aspect in line_split[2]:
                            unit = inner_tuples[tuple_iterator][1]
                            instance = line_split[1]
                            number = int(line_split[2][-1])
                            value = line_split[3][:-len(unit)]

                            self.alaign_table.insert(number, instance, value)
                            self.alaign_instances.add(instance)
                            return
                    if line_split[2] == aspect:
                        unit = inner_tuples[tuple_iterator][1]

                        instance = line_split[1]
                        util.inner_ord_set_insertion(self.instance_names, request_index, instance)

                        value = line_split[3][:-len(unit)]

                        # we want to convert b/s into MB/s, so if the unit is b/s, lower the value
                        # about factor 10^6.
                        # Pay attention, that this conversion implies an adaption in the visualizer
                        # module, where the unit is written out and also should be changed to MB/s!
                        if unit == 'b/s':
                            value = str(round(int(value) / 1000000))

                        util.tablelist_insertion(self.tables, request_index, recent_iteration,
                                                 instance, value)
                        if object_type == 'lun':
                            self.luns_available = True

                        return
                    request_index += 1
            else:
                request_index += len(PER_ITERATION_REQUESTS[object_type])

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
            self.lun_buffer = str(line.split()[2])
        elif 'LUN UUID: ' in line:
            if self.lun_buffer == '':
                raise InstanceNameNotFoundException
            else:
                lun_uuid = line.split()[2]
                self.lun_path_dict[lun_uuid] = self.lun_buffer
                self.lun_buffer = ''

    def rework_per_iteration_data(self, iteration_timestamps):
        """
        Simplifies data structures: Turns per_iteration_headers, which was a list of OrderedSets
        into a list of lists containing each header for each chart. In addition, flattens the table
        structure per_iteration_tables, so that each value row in the resulting csv tables will be
        represented by one list. Further, replaces the ID of each LUN in the headers with their
        paths for better readability.
        :param iteration_timestamps: The number of iterations
        :return: Two lists, representing per-iteration headers and values separately. The first list
        is nested once. Each inner list is a collection of table headers for one table. The second
        list is nested twice. The core lists are representations of one value row in one table. To
        separate several tables from each other, the next list level is used.
        """
        table_list = []
        for i in range(len(self.tables)):
            table_list.append(
                self.tables[i].flatten(self.instance_names[i], iteration_timestamps, 1))

        self.flat_headers = [table[0] for table in table_list]
        self.flat_values = [table[1] for table in table_list]

        flat_align_headers, flat_align_values = self.alaign_table.flatten(self.alaign_instances,
                                                                          None, 0)
        self.flat_headers.append(flat_align_headers)
        self.flat_values.append(flat_align_values)

        self.instance_names.append(self.alaign_instances)

        # replace lun's IDs in headers through their path names
        if 'lun' in PER_ITERATION_REQUESTS and self.luns_available:
            self.replace_lun_ids(self.flat_headers)

    def replace_lun_ids(self, header_list):
        """
        All values in PerfStat corresponding to LUNs are given in relation to their UUID, not their
        name or path. To make the resulting charts more readable, this function replaces their IDs
        with the paths.
        :param header_list: A list of lists which contains all instance names, the program
        found values for.
        :return: None.
        """

        index_first_lun_request = 0
        for object_type in PER_ITERATION_REQUESTS:
            if object_type != 'lun':
                for _ in PER_ITERATION_REQUESTS[object_type]:
                    index_first_lun_request += 1
        for i in range(len(PER_ITERATION_REQUESTS['lun'])):
            insertion_index = index_first_lun_request + i
            header_replacement = []
            for uuid in self.instance_names[insertion_index]:
                if uuid in self.lun_path_dict:
                    header_replacement.append(self.lun_path_dict[uuid])
                else:
                    raise InstanceNameNotFoundException(uuid)
            header_list[insertion_index] = header_replacement
