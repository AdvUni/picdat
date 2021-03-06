"""
Is responsible for collecting all information of note from PerfStat output
"""
import logging
import sys

from perfstat_mode.sysstat_container import SysstatContainer
from perfstat_mode.statit_container import StatitContainer
from perfstat_mode.per_iteration_container import PerIterationContainer
from perfstat_mode import per_iteration_container as per_iteration_module
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

    return 0


def found_iteration_begin(line, start_times, last_end_time):
    """
    Searches for an iteration begin marker in a string and, if applicable,
    adds the timestamp given in this marker to start_times.
    :param line: A string from a PerfStat output file which should be searched
    :param start_times: A list of all iteration start timestamps
    :param last_end_time: The last collected timestamp of an iteration's end. It would be
    used as recent timestamp, in case that there is no timestamp available in line on account of
    a PerfStat bug.
    :return: True, if the line contains an iteration begin marker, or False otherwise
    """
    if 'BEGIN Iteration' in line:
        start_times.append(per_iteration_module.get_iteration_timestamp(line, last_end_time))
        return True

    return False


def found_iteration_end(line, end_times, last_start_time):
    """
    Searches for an iteration end marker in a string and, if applicable,
    adds the timestamp given in this marker to end_times.
    :param line: A string from a PerfStat output file which should be searched
    :param end_times: A list of all iteration end timestamps
    :param last_start_time: The last collected timestamp of an iteration's beginning. It would be
    used as recent timestamp, in case that there is no timestamp available in line on account of
    a PerfStat bug.
    :return: True, if the line contains an iteration end marker, or False otherwise
    """
    if 'END Iteration' in line:
        end_times.append(per_iteration_module.get_iteration_timestamp(line, last_start_time))
        return True

    return False


def final_iteration_validation(expected_iteration_number, iteration_beginnings, iteration_endings):
    """
    Test whether the PerfStat terminated and is complete
    :param expected_iteration_number: the iteration number as it is defined in the PerfStat
    output header
    :param iteration_beginnings: the number of iterations which were actually started
    :param iteration_endings: the number of iterations which actually terminated
    :return: a string which informs the user whether the data are complete and how they will be
    handled
    """
    if expected_iteration_number == iteration_beginnings == iteration_endings:
        logging.debug('Planned number of iterations was executed correctly.')
    elif expected_iteration_number != iteration_beginnings:
        logging.warning('Warning: PerfStat output is incomplete; some iterations weren\'t '
                        'executed. If there is an iteration which wasn\'t finished correctly, '
                        'it won\'t be considered in the resulting charts!')
    else:
        logging.warning('PerfStat output is incomplete; the last iteration didn\'t terminate. It '
                        'won\'t be considered in the resulting charts!')


def combine_results(per_iteration_container, sysstat_container, statit_container, end_times):
    """
    This function combines the contents of all three request types. This means, it sticks
    all tables together and packs meta data about the tables. This includes the global variable
    localtimezone.
    :param per_iteration_container: PerIterationContainer object that holds all relevant
    information about per_iteration_requests.
    :param sysstat_container: SysstatContainer objet that holds all relevant information about
    sysstat_requests.
    :param statit_container: StatitContainer object that holds all relevant inforamtion read from
    statit blocks.
    :param end_times: The end timestamps of all iterations; they are needed to rework the statit
    data.
    :return: All tables in one list and an identifier dict providing meta data for all tables
    """

    combined_tables = per_iteration_container.rework_per_iteration_data() + \
        sysstat_container.rework_sysstat_data() + \
        statit_container.rework_statit_data(end_times)

    p_i_identifiers, p_i_units, p_i_is_histo = per_iteration_container.get_labels()
    sy_identifiers, sy_units, sy_is_histo = sysstat_container.get_labels()
    st_identifiers, st_units, st_is_histo = statit_container.get_labels()

    combined_identifiers = p_i_identifiers + sy_identifiers + st_identifiers
    combined_units = p_i_units + sy_units + st_units
    combined_is_histo = p_i_is_histo + sy_is_histo + st_is_histo

    label_dict = {'identifiers': combined_identifiers, 'units': combined_units,
                  'is_histo': combined_is_histo, 'timezone': str(util.localtimezone)}

    logging.debug('time zone: %s', util.localtimezone)

    return combined_tables, label_dict


def read_data_file(perfstat_data_file, sort_columns_by_name):
    """
    Reads the requested information from a PerfStat output file and collects them into several lists
    :param perfstat_data_file: file which should be read
    :param sort_columns_by_name: Some of the charts may have a great amount of graphs. By
    default, PicDat sorts the corresponding legend entries by relevance, means the graph with the
    highest values in sum is displayed at the top of the legend. If you rather would sort them
    alphabetically, this boolean should be true.
    :return: A list of all collected values in a table format. Each table is a nested list as
    well; the values are grouped by rows. Additionally, it returns an identifier_dict which
    contains meta data such as axis labels or apprpriate file names for all tables.
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

    # this object collects all information the program finds outside of sysstat and statit blocks
    per_iteration_container = PerIterationContainer(sort_columns_by_name)

    # this object collects all information the program finds during processing sysstat_x_1sec blocks
    sysstat_container = SysstatContainer()

    # this object collects all information the program finds during processing statit blocks
    statit_container = StatitContainer(sort_columns_by_name)

    # collecting data

    with open(perfstat_data_file, 'r', encoding='ascii', errors='surrogateescape') as data:
        for line in data:
            if not sysstat_container.inside_sysstat_block \
            or not sysstat_container.sysstat_header_needed:
                line = line.strip()

            # first, search for the planned number of iteration in the file's header.
            # Once set, skip this check.
            if number_of_iterations == 0:
                number_of_iterations = search_for_number_of_iterations(line)
                continue

            if sysstat_container.inside_sysstat_block:
                if not line.startswith('node') and len(line.strip()) != 0:
                    sysstat_container.process_sysstat_block(line)
                continue

            if '=-=-=-=-=-=' in line:
                # filter for iteration beginnings and endings
                if len(end_times) == 0:
                    last_end_time = None
                else:
                    last_end_time = end_times[-1]
                if found_iteration_begin(line, start_times, last_end_time):
                    iteration_begin_counter += 1
                elif found_iteration_end(line, end_times, start_times[-1]):
                    iteration_end_counter += 1
                    # write an empty line into the sysstat tables to cut line in resulting charts
                    # between different iterations (not after the last):
                    if iteration_end_counter != number_of_iterations:
                        sysstat_container.add_empty_lines()

                elif sysstat_container.found_sysstat_1sec_begin(line):
                    sysstat_container.collect_sysstat_timestamp(next(data), start_times[-1])

                continue

            if statit_container.inside_statit_block:
                statit_container.process_disc_stats(line)
                continue

            if statit_container.check_statit_begin(line):
                continue
            if start_times:
                per_iteration_container.process_per_iteration_keys(line, start_times[-1])

    logging.debug('processor data: %s', str(per_iteration_container.processor_tables))

    # postprocessing

    if number_of_iterations == 0:
        logging.warning('The file you entered as PerfStat output doesn\'t even contain, how many '
                        'iterations it handles. Maybe, it isn\'t a PerfStat file at all.')
        sys.exit(1)

    final_iteration_validation(number_of_iterations, iteration_begin_counter, iteration_end_counter)

    return combine_results(per_iteration_container, sysstat_container, statit_container, end_times)
