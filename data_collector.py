"""
Is responsible for collecting all information of note from PerfStat output
"""
import re

import util
import data_collector_util
from exceptions import InstanceNameNotFoundException

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


def process_per_iteration_requests(line, per_iteration_requests, recent_iteration, headers_sets,
                                   per_iteration_tables):
    """
    Searches a String for all per_iteration_requests from main. In case it finds something,
    it writes the results into the correct place in table_values. During the first iteration it
    collects the instance names of all requested object types as well and writes them into
    table_headers.
    :param line: A string from a PerfStat output file which should be searched
    :param per_iteration_requests: A data structure carrying all requests for data, the tool is
    going to collect once per iteration. It's an OrderedDict of lists which contains all requested
    object types mapped to the relating aspects and units which the tool should create graphs for.
    :param recent_iteration: An integer which says, in which perfStat iteration the function call
    happened
    :param headers_sets: A list of OrderedSets which contains all previous collected instance
    names, the program has values for in table_values.
    :param per_iteration_tables: A list of tables which contains all previous collected values.
    Each inner list contains all values relating on exact one per_iteration_request.
    :return: None
    """
    request_index = 0
    for object_type in per_iteration_requests:
        if object_type + ':' in line:
            inner_tuples = per_iteration_requests[object_type]

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
                    return
                request_index += 1
        else:
            request_index += len(per_iteration_requests[object_type])


def process_sysstat_requests(value_line, sysstat_percent_indices, sysstat_mbs_indices,
                             sysstat_percent_values, sysstat_mbs_values):
    """
    This function collects all relevant information from a line in a sysstat_x_1sec block. In
    case, the line doesn't contain values, but a sub header, the function ignores it.
    :param value_line: A String which is a line from a sysstat_x_1sec block
    :param sysstat_percent_indices: A list of numbers. They index the numbers of columns which
    contain values for the sysstat percent chart.
    :param sysstat_mbs_indices: A list of numbers. They index the numbers of columns which
    contain values for the sysstat MB/s chart.
    :param sysstat_percent_values: A list, holding tuples of values for the percent chart,
    grouped like the lines in the sysstat block. This function will append one tuple to the list.
    :param sysstat_mbs_values: A list, holding tuples of values for the MB/s chart, grouped like
    the lines in the sysstat block. This function will append one tuple to the list.
    :return: None
    """
    line_split = value_line.split()

    if str.isdigit(line_split[0].strip('%')):
        sysstat_percent_values.append(tuple([line_split[index].strip('%') for index in
                                             sysstat_percent_indices]))
        sysstat_mbs_values.append(tuple([line_split[index] for index in sysstat_mbs_indices]))


def process_sysstat_header(first_header_line, second_header_line, sysstat_percent_requests,
                           sysstat_mbs_requests):
    """
    Searches the header of a sysstat_x_1sec block, which is usually split over two lines,
    for the requested columns. Saves the headers matching the requests to lists. Also saves the
    column numbers belonging to those headers.
    :param first_header_line: The first line of a sysstat_x_1sec header
    :param second_header_line: The second line of a sysstat_x_1sec header
    :param sysstat_percent_requests: A list of tuples. Each tuple contains the name of a
    measurement in the first place and an additional identifier, which appears in the second
    header line, in the second place. The expected unit of these measurements is %. The data for
    them should appear in one chart together.
    matching to sysstat_percent_requests.
    indices belonging to sysstat_percent_headers in the same order.
    :param sysstat_mbs_requests: A list of tuples. Each tuple contains the name of a
    measurement in the first place. In the second place is another tuple, containing two
    parameters, e.g. 'read' and 'write'. The expected unit of these measurements is kB/s,
    but will be converted into MB/s. The data for them should appear in one chart together.
    matching to sysstat_mbs_requests.
    indices belonging to sysstat_mbs_headers in the same order.
    :return: Quadruple of the lists sysstat_percent_headers, sysstat_mbs_headers,
    sysstat_percent_indices and sysstat_mbs_indices. sysstat_percent_headers contains all headers
    matching to sysstat_percent_requests. sysstat_mbs_headers contains all headers
    matching to sysstat_mbs_requests. sysstat_percent_indices contains all column
    indices belonging to sysstat_percent_headers in the same order. sysstat_mbs_indices contains
    all column indices belonging to sysstat_mbs_headers in the same order.
    """

    # initalisation

    sysstat_percent_headers = []
    sysstat_percent_indices = []
    sysstat_mbs_headers = []
    sysstat_mbs_indices = []

    # Split the first line into single words and save them to header_line_split.
    # Simultaneously, memorize the line indices, at which the words end, into endpoints.
    header_line_split, endpoints = zip(
        *[(m.group(0), m.end()) for m in re.finditer(r'\S+', first_header_line)])

    # iterate over header_line_split:
    for index in range(len(header_line_split)):

        # iterate over the sysstat requests, which belong to the unit %:
        for request in sysstat_percent_requests:
            if data_collector_util.check_column_header(header_line_split[index], endpoints[index],
                                                       second_header_line, request[0], request[1]):
                if request[1] == ' ':
                    sysstat_percent_headers.append(request[0])
                else:
                    sysstat_percent_headers.append(str(request[0]) + '_' + str(request[1]))
                sysstat_percent_indices.append(index)

        # iterate over the sysstat requests, which belong to the unit MB/s:
        for request in sysstat_mbs_requests:
            if data_collector_util.check_column_header(header_line_split[index], endpoints[index],
                                                       second_header_line, request[0],
                                                       request[1][0]):
                sysstat_mbs_headers.append(str(request[0]) + '_' + str(request[1][0]))
                sysstat_mbs_indices.append(index)
                # Measurements for the MB/s chart always come with two parameters, e.g. 'read' and
                # 'write'. There is no way to read them from the header lines separately,
                # so we find them and add their columns to header_list and index_list at once
                sysstat_mbs_headers.append(str(request[0]) + '_' + str(request[1][1]))
                sysstat_mbs_indices.append(index + 1)

    return (
        sysstat_percent_headers, sysstat_mbs_headers, sysstat_percent_indices, sysstat_mbs_indices)


def replace_lun_ids(per_iteration_requests, header_row_list, lun_path_dict):
    """
    All values in PerfStat corresponding to LUNs are given in relation to their UUID, not their
    name or path. To make the resulting charts more readable, this function replaces their IDs
    with the paths.
    :param per_iteration_requests: A data structure carrying all requests for data, the tool is
    going to collect once per iteration. It's an OrderedDict of lists which contains all requested
    object types mapped to the relating aspects and units which the tool should create graphs for.
    :param header_row_list: A list of lists which contains all instance names, the program
    found values for.
    :param lun_path_dict: A dictionary translating the LUNs IDs into their paths.
    :return: The manipulated table_headers.
    """
    if 'lun' in per_iteration_requests:

        index_first_lun_request = 0
        for object_type in per_iteration_requests:
            if object_type != 'lun':
                for _ in per_iteration_requests[object_type]:
                    index_first_lun_request += 1

        for i in range(len(per_iteration_requests['lun'])):

            insertion_index = index_first_lun_request + i

            header_replacement = []
            for uuid in header_row_list[insertion_index]:
                if uuid in lun_path_dict:
                    header_replacement.append(lun_path_dict[uuid])
                else:
                    raise InstanceNameNotFoundException(uuid)
            header_row_list[insertion_index] = header_replacement

    return header_row_list


def postprocessing_per_iteration_data(per_iteration_tables, per_iteration_headers, iterations,
                                      per_iteration_requests, lun_path_dict):
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
    :param iterations: The number of iterations
    :param per_iteration_requests: A data structure carrying all requests for data, the tool is
    going to collect once per iteration. It's an OrderedDict of lists which contains all requested
    object types mapped to the relating aspects and units which the tool should create graphs for.
    :param lun_path_dict: A dictionary translating the LUNs IDs into their paths.
    :return: Two lists, representing per-iteration headers and values separately. The first list
    is nested once. Each inner list is a collection of table headers for one table. The second
    list is nested twice. The core lists are representations of one value row in one table. To
    separate several tables from each other, the next list level is used.
    """
    table_list = []
    for i in range(len(per_iteration_tables)):
        table_list.append(per_iteration_tables[i].get_rows(per_iteration_headers[i], iterations))

    header_row_list = [table[0] for table in table_list]
    value_rows_list = [table[1] for table in table_list]

    # replace lun's IDs in headers through their path names
    replace_lun_ids(per_iteration_requests, header_row_list, lun_path_dict)

    return header_row_list, value_rows_list


def read_data_file(perfstat_data_file, per_iteration_requests):
    """
    Reads the requested information from a PerfStat output file and collects them into several lists
    :param perfstat_data_file: file which should be read
    :param per_iteration_requests: A data structure carrying all requests for data, the tool is
    going to collect once per iteration. It's an OrderedDict of lists which contains all requested
    object types mapped to the relating aspects and units which the tool should create graphs for.
    :return: all information needed to write the csv tables, packed in a tuple
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

    # boolean, whether program is currently reading in a sysstat_x_1sec block:
    inside_sysstat_block = False

    # time stamps which mark the beginnings of a sysstat_x_1sec block:
    sysstat_times = []

    per_iteration_tables = []
    per_iteration_headers = []

    lun_path_dict = {}

    # collecting data

    with open(perfstat_data_file, 'r') as data:

        lun_path = ''

        for line in data:
            line = line.strip()

            # first, search for the planned number of iteration in the file's header.
            # Once set, skip this check.
            if number_of_iterations == 0:
                number_of_iterations = search_for_number_of_iterations(line)

            # '--' marks, that a sysstat_x_1sec block ends.
            elif line == '--':
                inside_sysstat_block = False

            elif inside_sysstat_block:
                # TODO: process sysstat_requests
                pass
            elif '=-=-=-=-=-=' in line:
                # filter for iteration beginnings and endings
                if found_iteration_begin(line, start_times):
                    iteration_begin_counter += 1
                elif found_iteration_end(line, end_times):
                    iteration_end_counter += 1
                elif found_sysstat_1sec_begin(line):
                    inside_sysstat_block = True
                    sysstat_times.append(data_collector_util.get_sysstat_timestamp(next(data)))
                    next(data)

            elif 'LUN ' in line:
                lun_path = map_lun_path(line, lun_path, lun_path_dict)

            # filter for the values you wish to visualize
            else:
                process_per_iteration_requests(line, per_iteration_requests,
                                               iteration_begin_counter, per_iteration_headers,
                                               per_iteration_tables)
    data.close()

    # print('sysstat_times: ' + str(sysstat_times))
    # print('iteration begins:' + str(start_times))
    # print('iteration ends:' + str(end_times))

    # postprocessing

    if number_of_iterations == 0:
        print('''The file you entered as PerfStat output doesn't even contain, how many
        iterations it handles.
        Maybe, it isn't a PerfStat file at all.''')

    data_collector_util.final_iteration_validation(number_of_iterations, iteration_begin_counter,
                                                   iteration_end_counter)

    # simplify data structures
    per_iteration_headers, per_iteration_values = postprocessing_per_iteration_data(
        per_iteration_tables, per_iteration_headers, iteration_begin_counter,
        per_iteration_requests, lun_path_dict)

    return start_times, per_iteration_headers, per_iteration_values
