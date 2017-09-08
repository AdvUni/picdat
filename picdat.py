"""
From here, the tool gets started.
"""
import os
import shutil
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


def take_perfstats():
    """
    This function requests a PerfStat output location of the user and decides, whether its type is
    data or zip. If applicable, it extracts the zip folder into a temporary directory.
    :return: The temporary directory's path (might be None, after usage of files inside this
    directory should become deleted) and a list of all PerfStat data files extracted from user
    input.
    """
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
            print('Extract zip...')
            temp_path, perfstat_output_files = util.extract_to_temp_dir(entered_file)
        else:
            print('Unexpected data type: File must be of type .data or .zip. Try again.')
            continue

        break

    return temp_path, perfstat_output_files


def take_directory():
    """
    This function requests a destination directory of the user. All results of the PicDat program
    will be written to this directory. If the directory doesn't exist yet, the function asks the
    user for creating it.
    :return: 
    """
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
    return destination_directory


def run():
    """
    The tool's main routine. Calls all functions to read the data, write CSVs
    and finally create an HTML. Handles user communication.
    :param per_iteration_requests: A data structure carrying all requests for data, the tool is
    going to collect once per iteration. It's an OrderedDict of lists which contains all requested
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

    # receive PerfStat file(s) from user:
    temp_path, perfstat_output_files = take_perfstats()

    # receive destination directory from user
    destination_directory = take_directory()

    # create directory and copy the necessary dygraphs files into it
    print('Prepare directory...')
    final_dest_directory = util.empty_directory(destination_directory)
    dygraphs_js_dest = final_dest_directory + os.sep + 'dygraph.js'
    dygraphs_css_dest = final_dest_directory + os.sep + 'dygraph.css'
    copyfile(constants.DYGRAPHS_JS_SRC, dygraphs_js_dest)
    copyfile(constants.DYGRAPHS_CSS_SRC, dygraphs_css_dest)

    counter = 0
    for perfstat_output in perfstat_output_files:

        # get absolute path for PerfStat source (just for using it as caption in resulting html)
        perfstat_output_absolute_path = os.path.abspath(perfstat_output)

        # collect data from file
        print('Read data...')
        table_headers, table_values = \
            data_collector.read_data_file(perfstat_output)

        # frame html file path
        html_filepath = final_dest_directory + os.sep + constants.HTML_FILENAME + str(
            counter) + constants.HTML_ENDING

        # generate file names for csv tables
        csv_filenames = util.get_csv_filenames(counter)
        csv_filepaths = [final_dest_directory + os.sep + filename for filename in csv_filenames]

        # write data into csv tables
        print('Create csv tables...')
        table_writer.create_csv(csv_filepaths, table_headers, table_values)

        # write html file
        print('Create html file...')
        visualizer.create_html(html_filepath, csv_filenames, table_headers,
                               perfstat_output_absolute_path)

        counter += 1

    # finally
    if temp_path is not None:
        shutil.rmtree(temp_path)
    print('Done. You will find charts under: ' + os.path.abspath(final_dest_directory))


# run
run()
