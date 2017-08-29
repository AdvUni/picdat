"""
Is responsible for collecting all information of note from PerfStat output
"""

import util
import data_collector_util
from exceptions import InvalidDataInputException, InstanceNameNotFoundException

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
    :return: the planned number of iteration, if given, or zero, otherwise
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
    :return: True, if the line contains an iteration begin marker and False, otherwise
    """
    if 'BEGIN Iteration' in line:
        start_times.append(data_collector_util.build_date(line))
        return True
    else:
        return False


def found_iteration_end(line, end_times):
    """
    Searches for an iteration end marker in a string and, if applicable,
    adds the timestamp given in this marker to end_times.
    :param line: A string from a PerfStat output file which should be searched
    :param end_times: A list of all iteration end timestamps
    :return: True, if the line contains an iteration end marker and False, otherwise
    """
    if 'END Iteration' in line:
        end_times.append(data_collector_util.build_date(line))
        return True
    else:
        return False


def map_lun_path(line, lun_path, lun_path_dict):
    """
    Builds a dictionary to translate each LUN's uuid into it's path for better readability.
    Looks for a 'LUN Path' or a 'LUN UUID' keyword. In case it found a path, it buffers the
    path name. In case a uuid was found, it writes the uuid in the lun_path_dict together with
    the lun path name buffered last.
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


def process_search_requests(line, search_requests, recent_iteration, headers_sets, table_values):
    """
    Searches a String for all search requests from main. In case it found something, it writes the
    results into the correct place in table_values. During the first iteration it collects the
    instance names of all requested object types as well and writes them into table_headers.
    :param line: A string from a PerfStat output file which should be searched
    :param search_requests: An OrderedDict of lists which contains all requested object types
    mapped to the relating aspects and units which the tool should create graphs for.
    :param recent_iteration: An integer which says, in which perfStat iteration the function call
    happened
    :param headers_sets: A list of OrderedSets which contains all previous collected instance
    names, the program has values for in table_values.
    :param table_values: A list of lists which contains all previous collected values.
    Each inner list contains all values relating on exact one search request.
    :return: None
    """
    request_index = 0
    for object_type in search_requests:
        if object_type + ':' in line:
            inner_tuples = search_requests[object_type]

            for tuple_iterator in range(len(inner_tuples)):
                aspect = inner_tuples[tuple_iterator][0]
                if ':' + aspect + ':' in line:
                    unit = inner_tuples[tuple_iterator][1]

                    instance = (line[len(object_type) + 1: line.index(aspect) - 1])
                    util.inner_ord_set_insertion(headers_sets, request_index, instance)

                    value = line[line.index(aspect) + len(aspect) + 1: line.index(unit)]
                    util.tablelist_insertion(table_values, request_index, recent_iteration,
                                             instance, value)
                    # print(object_type,aspect,request_index)
                    return
                # print('inner' + str(request_index))
                request_index += 1
        else:
            request_index += len(search_requests[object_type])
            # print('outer' + str(request_index))


def replace_lun_ids(search_requests, header_row_list, lun_path_dict):
    """
    All values in PerfStat corresponding to LUNs are given in relation to their UUID, not their
    name or path. To make the resulting charts more readable, this function replaces their IDs
    through the paths.
    :param search_requests: An OrderedDict of lists which contains all requested object types
    mapped to the relating aspects and units which the tool should create charts for.
    :param header_row_list: A list of lists which contains all instance names, the program
    found values for.
    :param lun_path_dict: A dictionary translating the LUNs IDs into their paths.
    :return: The manipulated table_headers.
    """
    if 'lun' in search_requests:

        index_first_lun_request = 0
        for object_type in search_requests:
            if object_type != 'lun':
                for _ in search_requests[object_type]:
                    index_first_lun_request += 1

        for i in range(len(search_requests['lun'])):

            insertion_index = index_first_lun_request + i

            header_replacement = []
            for uuid in header_row_list[insertion_index]:
                if uuid in lun_path_dict:
                    header_replacement.append(lun_path_dict[uuid])
                else:
                    raise InstanceNameNotFoundException(uuid)
            header_row_list[insertion_index] = header_replacement

    return header_row_list


def read_data_file(perfstat_data_file, search_requests):
    """
    reads the requested information from a PerfStat output file and collects them into several lists
    :param perfstat_data_file: file which should be read
    :param search_requests: An OrderedDict of lists which contains all requested object types
    mapped to the relating aspects and units which the tool should create graphs for.
    :return: all information needed to write the csv tables: table headers, table values,
    and the iterations start times, all packed in a dictionary.
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

    table_content = []
    header_sets = []

    lun_path = ''
    lun_path_dict = {}

    # collecting data

    with open(perfstat_data_file, 'r') as data:

        for line in data:
            line = line.strip()
            # first, search for the planned number of iteration in the file's header.
            # Once set, skip this check.
            if number_of_iterations == 0:
                try:
                    number_of_iterations = search_for_number_of_iterations(line)
                except ValueError:
                    raise InvalidDataInputException(perfstat_data_file)

            elif '=-=-=-=-=-=' in line:
                # filter for iteration beginnings and endings
                if found_iteration_begin(line, start_times):
                    iteration_begin_counter += 1
                elif found_iteration_end(line, end_times):
                    iteration_end_counter += 1

            elif 'LUN ' in line:
                lun_path = map_lun_path(line, lun_path, lun_path_dict)

            # filter for the values you wish to visualize
            else:
                process_search_requests(line, search_requests, iteration_begin_counter, header_sets,
                                        table_content)
    data.close()

    # postprocessing

    if number_of_iterations == 0:
        raise InvalidDataInputException(perfstat_data_file)

    data_collector_util.final_iteration_validation(number_of_iterations, iteration_begin_counter,
                                                   iteration_end_counter)

    # reformat tables data: flatten the table data structure to lists and finally seperate header
    #  content and value content in two lists

    table_list = []
    for i in range(len(table_content)):
        table_list.append(table_content[i].get_rows(header_sets[i], iteration_begin_counter))

    header_row_list = [table[0] for table in table_list]
    value_rows_list = [table[1] for table in table_list]

    # replace lun's IDs in headers through their path names
    replace_lun_ids(search_requests, header_row_list, lun_path_dict)

    return {'tables_headers': header_row_list, 'tables_content': value_rows_list,
            'timestamps': start_times}
