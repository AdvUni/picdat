"""
Is responsible for collecting all information of note from PerfStat output
"""
import data_collector_util
from sysstat_object import SysstatObject
from disk_statistics_object import DiskStatsObject
from per_iteration_object import PerIterationObject

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

    # per_iteration_tables = []
    # per_iteration_headers = []
    # this object collects all information the program finds outside of sysstat and statit blocks
    per_iteration_object = PerIterationObject()

    # this object collects all information the program finds during processing sysstat_x_1sec blocks
    sysstat_object = SysstatObject()

    # this object collects all information the program finds during processing statit blocks
    statit_object = DiskStatsObject()

    # a dictionary to hold the translations of the lun's IDs into their path names
    # lun_path_dict = {}

    # some PerfStat don't contain any values for luns. To prevent program from collapsing in this
    # case, following boolean will turn to True, as soon as a lun value appears in the PerfStat
    # luns_available = False

    # collecting data

    with open(perfstat_data_file, 'r') as data:

        for line in data:
            if not sysstat_object.inside_sysstat_block or not sysstat_object.sysstat_header_needed:
                line = line.strip()

            # first, search for the planned number of iteration in the file's header.
            # Once set, skip this check.
            if number_of_iterations == 0:
                number_of_iterations = search_for_number_of_iterations(line)
                continue

            if sysstat_object.inside_sysstat_block:
                sysstat_object.process_sysstat_block(line)

            if '=-=-=-=-=-=' in line:
                # filter for iteration beginnings and endings
                if found_iteration_begin(line, start_times):
                    iteration_begin_counter += 1
                elif found_iteration_end(line, end_times):
                    iteration_end_counter += 1
                    # write an empty line into the sysstat tables to cut line in resulting charts
                    # between different iterations (not after the last):
                    if iteration_end_counter != number_of_iterations:
                        sysstat_object.add_empty_lines()

                elif found_sysstat_1sec_begin(line):
                    sysstat_object.inside_sysstat_block = True
                    sysstat_object.recent_timestamp = data_collector_util.get_sysstat_timestamp(
                        next(data))
                    next(data)
                continue

            if statit_object.inside_statit_block:
                statit_object.process_disc_stats(line)
                continue

            if statit_object.check_statit_begin(line):
                continue

            per_iteration_object.process_per_iteration_requests(line, iteration_begin_counter)

    data.close()

    # postprocessing

    if number_of_iterations == 0:
        print('''The file you entered as PerfStat output doesn't even contain, how many
        iterations it handles.
        Maybe, it isn't a PerfStat file at all.''')

    data_collector_util.final_iteration_validation(number_of_iterations, iteration_begin_counter,
                                                   iteration_end_counter)

    # simplify data structures for per-iteration data
    per_iteration_headers, per_iteration_values = per_iteration_object.rework_per_iteration_data(
        start_times)

    statit_headers, statit_values = statit_object.flatten_table()

    return combine_results(per_iteration_headers, per_iteration_values,
                           sysstat_object.percent_headers, sysstat_object.percent_values,
                           sysstat_object.mbs_headers, sysstat_object.mbs_values,
                           sysstat_object.iops_headers, sysstat_object.iops_values,
                           statit_headers, statit_values), per_iteration_object.luns_available
