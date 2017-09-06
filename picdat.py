"""
From here, the tool gets started.
"""
import os
from shutil import copyfile
from collections import OrderedDict

import constants
import util
import data_collector
import table_writer
import visualizer

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


def init(per_iteration_requests):
    """
    Sets the value for per_iteration_request.
    :param per_iteration_requests: Empty OrderedDict.
    :return: None
    """
    per_iteration_requests['aggregate'] = [('total_transfers', '/s')]
    per_iteration_requests['processor'] = [('processor_busy', '%')]
    per_iteration_requests['volume'] = [('total_ops', '/s'), ('avg_latency', 'us'),
                                        ('read_data', 'b/s')]
    per_iteration_requests['lun'] = [('total_ops', '/s'), ('avg_latency', 'ms'),
                                     ('read_data', 'b/s')]


def run(per_iteration_requests, sysstat_percent_requests, sysstat_mbs_requests):
    """
    The tool's main routine. Calls all functions to read the data, write CSVs
    and finally create an HTML. Handles user communication.
    :param per_iteration_requests: A data structure carrying all requests for data, the tool is going
    to collect once per iteration. It's an OrderedDict of lists which contains all requested 
    object types mapped to the relating aspects and units which the tool should create graphs for.
    :param sysstat_percent_requests: A list of tuples. Each tuple contains the name of a
    measurement in the first place and an additional identifier, which appears in the second
    header line, in the second place. The expected unit of these measurements is %. The data for
    them should appear in one chart together.
    :param sysstat_mbs_requests: A list of tuples. Each tuple contains the name of a
    measurement in the first place. In the second place is another tuple, containing two
    parameters, e.g. 'read' and 'write'. The expected unit of these measurements is kB/s,
    but will be converted into MB/s. The data for them should appear in one chart together.
    :return: None
    """

    print('Welcome to PicDat!')

    # receive PerfStat file from user:
    perfstat_output_files = None
    temp_path = None
    while True:
        entered_file = input('Please enter a path to a PerfStat output file: ')
        if entered_file == '':
            entered_file = constants.DEFAULT_PERFSTAT_OUTPUT_FILE
        elif not os.path.isfile(entered_file):
            print('This file does not exist. Try again.')
            continue

        if util.data_type(entered_file) == 'data':
            perfstat_output_files = [entered_file]
        elif util.data_type(entered_file) == 'zip':
            temp_path, perfstat_output_files = util.copy_to_temp_dir(entered_file)
        else:
            print('Unexpected data type: File must be of type .data or .zip. Try again.')
            continue

        break

    # receive destination directory from user
    while True:
        destination_directory = input('Please select a destination directory for the results: ')
        if destination_directory != '':
            if os.path.isdir(destination_directory):
                destination_directory += os.sep
                break
            elif input('This directory does not exist. Would you like to create it? (Enter y) ') \
                    == 'y':
                os.makedirs(destination_directory)
                print('Created directory ' + destination_directory)
                destination_directory += os.sep
                break
            else:
                print('So, try again.')
        else:
            break

    destination_directory += constants.DEFAULT_DIRECTORY_NAME

    # create directory and copy the necessary dygraphs files into it
    print('Prepare directory...')
    final_dest_directory = util.empty_directory(destination_directory)
    dygraphs_js_dest = final_dest_directory + os.sep + 'dygraph.js'
    dygraphs_css_dest = final_dest_directory + os.sep + 'dygraph.css'
    copyfile(constants.DYGRAPHS_JS_SRC, dygraphs_js_dest)
    copyfile(constants.DYGRAPHS_CSS_SRC, dygraphs_css_dest)

    print(perfstat_output_files)

    counter = 0
    for perfstat_output in perfstat_output_files:
        print(perfstat_output)

        # get absolute path for PerfStat data file (just for using it as caption in resulting html)
        perfstat_output_absolute_path = os.path.abspath(perfstat_output)

        # collect data from file
        print('Read data...')
        table_headers, table_values = \
            data_collector.read_data_file(perfstat_output, per_iteration_requests,
                                          sysstat_percent_requests, sysstat_mbs_requests)

        # frame html file path
        html_filepath = final_dest_directory + os.sep + constants.HTML_FILENAME + str(
            counter) + constants.HTML_ENDING

        # generate file names for csv tables
        csv_filenames = util.get_csv_filenames(counter, per_iteration_requests)
        csv_filepaths = [final_dest_directory + os.sep + filename for filename in csv_filenames]

        # write data into csv tables
        print('Create csv tables...')
        table_writer.create_csv(csv_filepaths, table_headers, table_values)

        # write html file
        print('Create html file...')
        visualizer.create_html(html_filepath, csv_filenames, per_iteration_requests,
                               table_headers, perfstat_output_absolute_path)

        counter += 1

    # finally
    del temp_path
    print('Done. You will find charts under: ' + os.path.abspath(final_dest_directory))


# run
init_per_iteration_requests = OrderedDict()
init(init_per_iteration_requests)
run(init_per_iteration_requests, constants.SYSSTAT_PERCENT_REQUESTS, constants.SYSSTAT_MBS_REQUESTS)
