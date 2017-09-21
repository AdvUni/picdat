"""
From here, the tool gets started.
"""
import os
import shutil
from shutil import copyfile
import traceback

import sys

import constants
import global_vars
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
    while True:
        print('Please enter a path to a PerfStat output file')
        user_input = input('(data type .data or .zip):')

        if user_input == '':
            user_input = constants.DEFAULT_PERFSTAT_OUTPUT_FILE
        elif os.path.isdir(user_input):
            break
        elif not os.path.isfile(user_input):
            print('This file does not exist. Try again.')
            continue

        data_type = util.data_type(user_input)

        if data_type != 'data' and data_type != 'zip':
            print('Unexpected data type: File must be of type .data or .zip. Try again.')
            continue

        break

    return user_input


def take_directory():
    """
    This function requests a destination directory of the user. All results of the PicDat program
    will be written to this directory. If the directory doesn't exist yet, the function asks the
    user for creating it.
    :return: The path to the directory, the results should be written in
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

    return destination_directory


def prepare_directory(destination_dir):
    """
    Creates an empty directory inside the user-given directory, which isn't in use yet. Copies
    the dygraphs .jss and .css files into the new directory.
    :param destination_dir: The directory, the user gave in as destination.
    :return: The path to a directory inside destination_dir. In this directory, PicDat should
    write all results.
    """
    destination_dir += constants.DEFAULT_DIRECTORY_NAME

    print('Prepare directory...')
    results_dir = util.empty_directory(destination_dir)

    csv_dir = results_dir + os.sep + 'tables'
    os.makedirs(csv_dir)

    dygraphs_dir = results_dir + os.sep + 'dygraphs'
    os.makedirs(dygraphs_dir)

    dygraphs_js_source = util.get_base_path() + constants.DYGRAPHS_JS_SRC
    dygraphs_js_dest = dygraphs_dir + os.sep + 'dygraph.js'
    dygraphs_css_source = util.get_base_path() + constants.DYGRAPHS_CSS_SRC
    dygraphs_css_dest = dygraphs_dir + os.sep + 'dygraph.css'
    copyfile(dygraphs_js_source, dygraphs_js_dest)
    copyfile(dygraphs_css_source, dygraphs_css_dest)

    return results_dir, csv_dir


def run():
    """
    The tool's main routine. Calls all functions to read the data, write CSVs
    and finally create an HTML. Handles user communication.
    :return: None
    """
    temp_path = None
    console_file = None
    identifier_dict = None

    try:

        print('Welcome to PicDat!')

        # receive PerfStat file(s) from user:
        user_input = take_perfstats()

        # receive destination directory from user
        destination_directory = take_directory()

        # create directory and copy the necessary dygraphs files into it
        result_dir, csv_dir = prepare_directory(destination_directory)

        # extract zip if necessary
        perfstat_output_files = None
        if os.path.isdir(user_input):
            perfstat_output_files, console_file = util.get_all_output_files(user_input)
        elif util.data_type(user_input) == 'data':
            perfstat_output_files = [user_input]
        elif util.data_type(user_input) == 'zip':
            print('Extract zip...')
            temp_path, perfstat_output_files, console_file = util.extract_to_temp_dir(user_input)

        # interrupt program if there are no .data files found
        if not user_input:
            print('Info: The input you gave doesn\'t contain any .data files.')
            sys.exit(0)

        # if given, read cluster and node information from console.log file:
        if console_file is not None:
            print('Read console.log file for getting cluster and node names...')
            try:
                identifier_dict = util.read_console_file(console_file)
            except KeyboardInterrupt:
                raise
            except:
                print('Info: console.log file from zip couldn\'t be read for some reason:')
                print(traceback.format_exc())
                identifier_dict = None
        else:
            print('Info: Did not find a console.log file to extract perfstat\'s cluster and node '
                  'name.')

        for perfstat_node in perfstat_output_files:

            # get nice names (if possible) for each PerfStat and the whole html file
            if len(perfstat_output_files) > 0:
                perfstat_address = perfstat_node.split(os.sep)[-2]

                if identifier_dict is None:
                    html_title = perfstat_node
                    node_identifier = perfstat_address
                else:
                    try:
                        node_identifier = identifier_dict[perfstat_address][1]
                        html_title = util.get_html_title(identifier_dict, perfstat_address)
                    except (KeyError):
                        print('Info: Did not find a node name for address \'' + perfstat_address
                              + '\' in \'console.log\'. Will use just \'' + perfstat_address
                              + '\' instead.')
                        html_title = perfstat_node
                        node_identifier = perfstat_address

                print('Handle PerfStat from node "' + node_identifier + '":')
                node_identifier += '_'
            else:
                node_identifier = ''
                html_title = perfstat_node

            # collect data from file
            print('Read data...')
            (table_headers, table_values), luns_available = data_collector.read_data_file(
                perfstat_node)
            if not luns_available:
                print('Info: Seems like PerfStat doesn\'t contain any information about LUNs.')

            # frame html file path
            html_filepath = result_dir + os.sep + node_identifier + constants.HTML_FILENAME + \
                            constants.HTML_ENDING

            # generate file names for csv tables
            csv_filenames = util.get_csv_filenames(node_identifier, luns_available)
            csv_abs_filepaths = [csv_dir + os.sep + filename for filename in csv_filenames]
            csv_filelinks = [csv_dir.split(os.sep)[-1] + '/' + filename for filename in
                             csv_filenames]

            # write data into csv tables
            print('Create csv tables...')
            table_writer.create_csv(csv_abs_filepaths, table_headers, table_values)

            # write html file
            print('Create html file...')
            visualizer.create_html(html_filepath, csv_filelinks, table_headers,
                                   html_title, luns_available)

            # reset global variables
            global_vars.reset()

        print('Done. You will find charts under: ' + os.path.abspath(result_dir))

    finally:
        # delete extracted zip
        if temp_path is not None:
            print('Delete temporarily extracted files...')
            shutil.rmtree(temp_path)


# run
run()
