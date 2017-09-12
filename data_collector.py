"""
Is responsible for collecting all information of note from PerfStat output
"""
import constants
import util
import data_collector_util
from sysstat_object import SysstatObject
from disk_statistics_object import DiskStatsObject
from exceptions import InstanceNameNotFoundException
from requests import PER_ITERATION_REQUESTS

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


def search_for_number_of_iterations(line):
    """
    Recognizes and, if applicable, filters the number of iterations planned in a
    PerfStat measuring from a string.
    :param line: A string from a PerfStat output file which should be searched
    :return: the planned number of iteration, if given, or zero otherwise
    """
    if 'ITERATIONS,' in line:
        # get the 3rd word of this line, which should be the number of iterations
        number_string = (line.split()[2])
        # get rid of a quotation mark and parse to int
        return int(number_string[1:-1])
    else:
        return 0


def found_iteration_begin(line, start_times):
    """
    Searches for an iteration begin marker in a string and, if applicable,
    adds the timestamp given in this marker to start_times.
    :param line: A string from a PerfStat output file which should be searched
    :param start_times: A list of all iteration start timestamps
    :return: True, if the line contains an iteration begin marker, or False otherwise
    """
    if 'BEGIN Iteration' in line:
        start_times.append(data_collector_util.get_iteration_timestamp(line))
        return True
    else:
        return False


def found_iteration_end(line, end_times):
    """
    Searches for an iteration end marker in a string and, if applicable,
    adds the timestamp given in this marker to end_times.
    :param line: A string from a PerfStat output file which should be searched
    :param end_times: A list of all iteration end timestamps
    :return: True, if the line contains an iteration end marker, or False otherwise
    """
    if 'END Iteration' in line:
        end_times.append(data_collector_util.get_iteration_timestamp(line))
        return True
    else:
        return False


def found_sysstat_1sec_begin(line):
    """
    Looks, whether a String marks the beginning of a sysstat_x_1sec section.
    :param line: A string from a PerfStat output file which should be searched
    :return: True, if the line marks the beginning of a sysstat_x_1sec section, or False otherwise
    """
    return 'sysstat_x_1sec' in line


def map_lun_path(line, lun_path, lun_path_dict):
    """
    Builds a dictionary to translate each LUN's uuid into it's path for better readability.
    Looks for a 'LUN Path' or a 'LUN UUID' keyword. In case it finds a path, it buffers the
    path name. In case a uuid is found, it writes the uuid in the lun_path_dict together with
    the lun path name last buffered.
    :param line: A string from a PerfStat output file which should be searched
    :param lun_path: The last buffered lun_path
    :param lun_path_dict: The dict in which the uuid-path-pairs should be written in
    :return: a lun path string to buffer it until next method call
    """
    if 'LUN Path: ' in line:
        return str(line.split()[2])
    elif 'LUN UUID: ' in line:
        if lun_path == '':
            raise InstanceNameNotFoundException
        else:
            lun_uuid = line.split()[2]
            lun_path_dict[lun_uuid] = lun_path
            return str('')
    else:
        return lun_path


def process_per_iteration_requests(line, recent_iteration, headers_sets, per_iteration_tables):
    """
    Searches a String for all per_iteration_requests from main. In case it finds something,
    it writes the results into the correct place in table_values. During the first iteration it
    collects the instance names of all requested object types as well and writes them into
    table_headers.
    :param line: A string from a PerfStat output file which should be searched
    :param recent_iteration: An integer which says, in which perfStat iteration the function call
    happened
    :param headers_sets: A list of OrderedSets which contains all previous collected instance
    names, the program has values for in table_values.
    :param per_iteration_tables: A list of tables which contains all previous collected values.
    Each inner list contains all values relating on exact one per_iteration_request.
    :return: True, if it found a value for a lun and false otherwise.
    """
    request_index = 0
    for object_type in PER_ITERATION_REQUESTS:
        if object_type + ':' in line:
            inner_tuples = PER_ITERATION_REQUESTS[object_type]

            for tuple_iterator in range(len(inner_tuples)):
                aspect = inner_tuples[tuple_iterator][0]
                if ':' + aspect + ':' in line:
                    unit = inner_tuples[tuple_iterator][1]

                    instance = (line[len(object_type) + 1: line.index(aspect) - 1])
                    util.inner_ord_set_insertion(headers_sets, request_index, instance)

                    value = line[line.index(aspect) + len(aspect) + 1: line.index(unit)]

                    # we want to convert b/s into MB/s, so if the unit is b/s, lower the value
                    # about factor 10^6.
                    # Pay attention, that this conversion implies an adaption in the visualizer
                    # module, where the unit is written out and also should be changed to MB/s!!!
                    if unit == 'b/s':
                        value = str(round(int(value) / 1000000))

                    util.tablelist_insertion(per_iteration_tables, request_index, recent_iteration,
                                             instance, value)
                    return object_type == 'lun'
                request_index += 1
        else:
            request_index += len(PER_ITERATION_REQUESTS[object_type])


def replace_lun_ids(header_row_list, lun_path_dict):
    """
    All values in PerfStat corresponding to LUNs are given in relation to their UUID, not their
    name or path. To make the resulting charts more readable, this function replaces their IDs
    with the paths.
    :param header_row_list: A list of lists which contains all instance names, the program
    found values for.
    :param lun_path_dict: A dictionary translating the LUNs IDs into their paths.
    :param luns_available: A boolean, whether lun values appeared in the PerfStat at all.
    :return: The manipulated table_headers.
    """

    index_first_lun_request = 0
    for object_type in PER_ITERATION_REQUESTS:
        if object_type != 'lun':
            for _ in PER_ITERATION_REQUESTS[object_type]:
                index_first_lun_request += 1
    for i in range(len(PER_ITERATION_REQUESTS['lun'])):
        insertion_index = index_first_lun_request + i
        header_replacement = []
        for uuid in header_row_list[insertion_index]:
            if uuid in lun_path_dict:
                header_replacement.append(lun_path_dict[uuid])
            else:
                raise InstanceNameNotFoundException(uuid)
        header_row_list[insertion_index] = header_replacement

    return header_row_list


def rework_per_iteration_data(per_iteration_tables, per_iteration_headers,
                              iteration_timestamps, lun_path_dict, luns_available):
    """
    Simplifies data structures: Turns per_iteration_headers, which was a list of OrderedSets into
    a list of lists containing each header for each chart. In addition, flattens the table
    structure per_iteration_tables, so that each value row in the resulting csv tables will be
    represented by one list. Further, replaces the ID of each LUN in the headers with their
    paths for better readability.
    :param per_iteration_tables: A list from type 'Table'. It contains all
    per-iteration values collected from a PerfStat output file, grouped by iteration and instance.
    :param per_iteration_headers: A List of Sets containing all instance names (column names)
    occurring in one table.
    :param iteration_timestamps: The number of iterations
    :param lun_path_dict: A dictionary translating the LUNs IDs into their paths.
    :return: Two lists, representing per-iteration headers and values separately. The first list
    is nested once. Each inner list is a collection of table headers for one table. The second
    list is nested twice. The core lists are representations of one value row in one table. To
    separate several tables from each other, the next list level is used.
    :param luns_available: A boolean, whether lun values appeared in the PerfStat at all.
    """
    table_list = []
    for i in range(len(per_iteration_tables)):
        table_list.append(
            per_iteration_tables[i].get_rows(per_iteration_headers[i], iteration_timestamps))

    header_row_list = [table[0] for table in table_list]
    value_rows_list = [table[1] for table in table_list]

    # replace lun's IDs in headers through their path names
    if 'lun' in PER_ITERATION_REQUESTS and luns_available:
        replace_lun_ids(header_row_list, lun_path_dict)

    return header_row_list, value_rows_list


def combine_results(per_iteration_headers, per_iteration_values, sysstat_percent_headers,
                    sysstat_percent_values, sysstat_mbs_headers, sysstat_mbs_values,
                    sysstat_iops_headers, sysstat_iops_values, statit_headers, statit_values):
    """
    This function sticks the results of all three request types together.
    :param per_iteration_headers: A list of list, holding the headers for each per-iteration chart.
    :param per_iteration_values: A list, holding all values referring the per_iteration_requests.
    It's nested twice.
    :param sysstat_percent_headers: A list, holding the headers for the sysstat-percent chart.
    :param sysstat_percent_values: A list, holding lists of values for the percent chart,
    grouped like the lines in the sysstat block.
    :param sysstat_mbs_headers: A list, holding the headers for the sysstat-mbs chart.
    :param sysstat_mbs_values: A list, holding lists of values for the mbs chart,
    grouped like the lines in the sysstat block.
    :return: All headers in one list, followed by all values in one list.
    """
    combined_headers = per_iteration_headers + [sysstat_percent_headers, sysstat_mbs_headers,
                                                sysstat_iops_headers, statit_headers]
    combined_values = per_iteration_values + [sysstat_percent_values, sysstat_mbs_values,
                                              sysstat_iops_values, statit_values]

    return combined_headers, combined_values


def read_data_file(perfstat_data_file):
    """
    Reads the requested information from a PerfStat output file and collects them into several lists
    :param perfstat_data_file: file which should be read
    :return: a list of all headers and a list of all values. The headers are grouped by table.
    The values are grouped by table and by row. Each value row already starts with its timestamp.
    Additionally, it returns the luns_available boolean which says, whether lun values appeared in
    the PerfStat at all.
    """

    # initialisation

    # number of iterations like it is defined in the file's header:
    number_of_iterations = 0

    # number of iterations that actually has been started:
    iteration_begin_counter = 0
    # the relating time stamps:
    start_times = []

    # number of iterations that actually terminated:
    iteration_end_counter = 0
    # the relating time stamps:
    end_times = []

    # time stamps which mark the beginnings of a sysstat_x_1sec block:
    recent_sysstat_timestamp = None

    per_iteration_tables = []
    per_iteration_headers = []

    # this object collects all information the program finds during processing sysstat_x_1sec blocks
    sysstat_object = SysstatObject()

    # this object collects all information the program finds during processing statit blocks
    statit_object = DiskStatsObject()

    # a dictionary to hold the translations of the lun's IDs into their path names
    lun_path_dict = {}

    # some PerfStat don't contain any values for luns. To prevent program from collapsing in this
    # case, following boolean will turn to True, as soon as a lun value appears in the PerfStat
    luns_available = False

    # collecting data

    with open(perfstat_data_file, 'r') as data:

        lun_path = ''

        for line in data:
            if not sysstat_object.inside_sysstat_block or not sysstat_object.sysstat_header_needed:
                line = line.strip()

            # first, search for the planned number of iteration in the file's header.
            # Once set, skip this check.
            if number_of_iterations == 0:
                number_of_iterations = search_for_number_of_iterations(line)
                continue

            if sysstat_object.inside_sysstat_block:
                # '--' marks, that a sysstat_x_1sec block ends.
                if line == '--':
                    sysstat_object.inside_sysstat_block = False
                elif sysstat_object.sysstat_header_needed:
                    sysstat_object.process_sysstat_header(line, next(data))
                else:
                    if sysstat_object.process_sysstat_requests(line, recent_sysstat_timestamp):
                        recent_sysstat_timestamp += constants.ONE_SECOND
                continue

            if '=-=-=-=-=-=' in line:
                # filter for iteration beginnings and endings
                if found_iteration_begin(line, start_times):
                    iteration_begin_counter += 1
                elif found_iteration_end(line, end_times):
                    iteration_end_counter += 1
                    # write an empty line into the sysstat tables to cut line in resulting charts
                    #  between different iterations:
                    if iteration_end_counter != number_of_iterations:
                        sysstat_object.add_empty_lines()

                elif found_sysstat_1sec_begin(line):
                    sysstat_object.inside_sysstat_block = True
                    recent_sysstat_timestamp = data_collector_util.get_sysstat_timestamp(next(data))
                    next(data)
                continue

            if statit_object.inside_statit_block:
                statit_object.process_disc_stats(line)
                continue

            if statit_object.check_statit_begin(line):
                continue

            if 'LUN ' in line:
                lun_path = map_lun_path(line, lun_path, lun_path_dict)
                continue

            # filter for the values you wish to visualize
            if process_per_iteration_requests(line, iteration_begin_counter,
                                              per_iteration_headers, per_iteration_tables):
                luns_available = True
    data.close()

    # postprocessing

    if number_of_iterations == 0:
        print('''The file you entered as PerfStat output doesn't even contain, how many
        iterations it handles.
        Maybe, it isn't a PerfStat file at all.''')

    data_collector_util.final_iteration_validation(number_of_iterations, iteration_begin_counter,
                                                   iteration_end_counter)

    # simplify data structures for per-iteration data
    per_iteration_headers, per_iteration_values = rework_per_iteration_data(
        per_iteration_tables, per_iteration_headers, start_times, lun_path_dict, luns_available)

    statit_headers, statit_values = statit_object.flatten_table()

    return combine_results(per_iteration_headers, per_iteration_values,
                           sysstat_object.percent_headers, sysstat_object.percent_values,
                           sysstat_object.mbs_headers, sysstat_object.mbs_values,
                           sysstat_object.iops_headers, sysstat_object.iops_values,
                           statit_headers, statit_values), luns_available
