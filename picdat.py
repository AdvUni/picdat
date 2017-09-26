"""
From here, the tool gets started.
"""
import getopt
import logging
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


def print_help_and_exit(program_name):
    """
    This function prints a String about the program's usage to the command line and then quits 
    the program.
    :param program_name: The program's name.
    :return: None
    """
    print(constants.HELP % program_name)
    sys.exit(0)


def validate_input_file(input_file):
    """
    This function validates an input file given by the user with some simple criteria.
    :param input_file: The user-given input file
    :return: None
    :raises fileNotFoundError: raises an exception, if input_file is neither a directory nor a file.
    :raises typeError: raises an exception, if input_file is a file of the wrong data type
    (neither .data nor .zip).
    """
    if os.path.isdir(input_file):
        return
    elif not os.path.isfile(input_file):
        raise FileNotFoundError

    data_type = util.data_type(input_file)

    if data_type != 'data' and data_type != 'zip':
        raise TypeError


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
        input_file = input('(data type .data or .zip):')

        if input_file == '':
            input_file = constants.DEFAULT_PERFSTAT_OUTPUT_FILE

        try:
            validate_input_file(input_file)
            return input_file
        except FileNotFoundError:
            print('This file does not exist. Try again.')
        except TypeError:
            print('Unexpected data type: File must be of type .data or .zip. Try again.')


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
                break
            elif input('This directory does not exist. Would you like to create it? (Enter y) ') \
                    == 'y':
                os.makedirs(destination_directory)
                logging.info('Created directory %s', destination_directory)
                break
            else:
                print('So, try again.')
        else:
            destination_directory = 'results'
            break

    return destination_directory


def prepare_directory(destination_dir):
    """
    Copies the dygraphs .jss and .css files into the given directory. Also creates an empty
    subdirectory for csv tables.
    :param destination_dir: The directory, the user gave in as destination.
    :return: The path to the csv directory inside destination_dir. In this directory, PicDat should
    write all csv tables.
    """
    logging.info('Prepare directory...')

    csv_dir = destination_dir + os.sep + 'tables'
    if not os.path.isdir(csv_dir):
        os.makedirs(csv_dir)

    dygraphs_dir = destination_dir + os.sep + 'dygraphs'
    if not os.path.isdir(dygraphs_dir):
        os.makedirs(dygraphs_dir)

    dygraphs_js_source = util.get_base_path() + constants.DYGRAPHS_JS_SRC
    dygraphs_js_dest = dygraphs_dir + os.sep + 'dygraph.js'
    dygraphs_css_source = util.get_base_path() + constants.DYGRAPHS_CSS_SRC
    dygraphs_css_dest = dygraphs_dir + os.sep + 'dygraph.css'
    copyfile(dygraphs_js_source, dygraphs_js_dest)
    copyfile(dygraphs_css_source, dygraphs_css_dest)

    return csv_dir


def handle_user_input(argv):
    """
    Processes command line options belonging to PicDat. If no log level is given, takes default
    log level instead. If no input file or output directory is given, PicDat will ask the user
    about them at runtime. 
    :param argv: Command line options.
    :return: A tuple of two paths; the first one leads to the PerfStat input, the second one to
    the output directory.
    """

    # get all options from argv and turn them into a dict
    try:
        opts, _ = getopt.getopt(argv[1:], 'hd:i:o:', ['help', 'debug=', 'inputfile=', 'outputdir='])
        opts = dict(opts)
    except getopt.GetoptError:
        logging.exception('Couldn\'t read command line options.')
        print_help_and_exit(argv[0])

    # print help information if option 'help' is given
    if '-h' in opts or '--help' in opts:
        print_help_and_exit(argv[0])

    # extract log level from options if possible
    if '-d' in opts:
        log_level = util.get_log_level(opts['-d'])
    elif '--debug' in opts:
        log_level = util.get_log_level(opts['--debug'])
    else:
        log_level = constants.DEFAULT_LOG_LEVEL

    logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s', level=log_level)

    # extract inputfile from options if possible
    if '-i' in opts:
        input_file = opts['-i']
    elif '--inputfile' in opts:
        input_file = opts['--inputfile']
    else:
        input_file = take_perfstats()

    try:
        validate_input_file(input_file)
    except FileNotFoundError:
        logging.error('File %s does not exist.', input_file)
        sys.exit(1)
    except TypeError:
        logging.error('File %s is of unexpected data type.', input_file)
        sys.exit(1)

    # extract outputdir from options if possible
    if '-o' in opts:
        output_dir = opts['-o']
    elif '--outputdir' in opts:
        output_dir = opts['--outputdir']
    else:
        output_dir = take_directory()

    if not os.path.isdir(output_dir):
        os.makedirs(output_dir)

    return input_file, output_dir


def run(input_file, result_dir):
    """
    The tool's main routine. Calls all functions to read the data, write CSVs
    and finally create an HTML. Handles user communication.
    :return: None
    """
    temp_path = None
    console_file = None
    identifier_dict = None

    try:
        # create directory and copy the necessary dygraphs files into it
        csv_dir = prepare_directory(result_dir)

        # extract zip if necessary
        perfstat_output_files = None
        if os.path.isdir(input_file):
            perfstat_output_files, console_file = util.get_all_output_files(input_file)
        elif util.data_type(input_file) == 'data':
            perfstat_output_files = [input_file]
        elif util.data_type(input_file) == 'zip':
            logging.info('Extract zip...')
            temp_path, perfstat_output_files, console_file = util.extract_to_temp_dir(input_file)

        # interrupt program if there are no .data files found
        if not input_file:
            logging.info('The input you gave (%s) doesn\'t contain any .data files.', input_file)
            sys.exit(0)

        # if given, read cluster and node information from console.log file:
        if console_file is not None:
            logging.info('Read console.log file for getting cluster and node names...')
            try:
                identifier_dict = util.read_console_file(console_file)
            except KeyboardInterrupt:
                raise
            except:
                logging.info('console.log file from zip couldn\'t be read for some reason: %s',
                             traceback.format_exc())
                identifier_dict = None
        else:
            logging.info('Did not find a console.log file to extract perfstat\'s cluster and node '
                         'name.')

        for perfstat_node in perfstat_output_files:

            # get nice names (if possible) for each PerfStat and the whole html file
            if len(perfstat_output_files) > 1:
                perfstat_address = perfstat_node.split(os.sep)[-2]

                if identifier_dict is None:
                    html_title = perfstat_node
                    node_identifier = perfstat_address
                else:
                    try:
                        node_identifier = identifier_dict[perfstat_address][1]
                        html_title = util.get_html_title(identifier_dict, perfstat_address)
                    except KeyError:
                        logging.info(
                            'Did not find a node name for address \'%s\' in \'console.log\'. Will '
                            'use just \'%s\' instead.', perfstat_address, perfstat_address)
                        html_title = perfstat_node
                        node_identifier = perfstat_address

                    logging.info('Handle PerfStat from node "' + node_identifier + '":')
                node_identifier += '_'
            else:
                node_identifier = ''
                html_title = perfstat_node

            # collect data from file
            logging.info('Read data...')
            request_objects, table_headers, table_values = data_collector.read_data_file(
                perfstat_node)

            logging.debug('table_headers: %s', table_headers)
            logging.debug('table_values: %s', table_values)

            # frame html file path
            html_filepath = result_dir + os.sep + node_identifier + constants.HTML_FILENAME + \
                            constants.HTML_ENDING

            # generate file names for csv tables
            csv_filenames = util.get_csv_filenames(request_objects, node_identifier)
            csv_abs_filepaths = [csv_dir + os.sep + filename for filename in csv_filenames]
            csv_filelinks = [csv_dir.split(os.sep)[-1] + '/' + filename for filename in
                             csv_filenames]

            # write data into csv tables
            logging.info('Create csv tables...')
            table_writer.create_csv(csv_abs_filepaths, table_headers, table_values, request_objects)

            # write html file
            logging.info('Create html file...')
            visualizer.create_html(html_filepath, csv_filelinks, html_title, request_objects)

            # reset global variables
            global_vars.reset()

        logging.info('Done. You will find charts under: ' + os.path.abspath(result_dir))

    finally:
        # delete extracted zip
        if temp_path is not None:
            shutil.rmtree(temp_path)
            logging.info('(Temporarily extracted files deleted)')


# run
user_input = handle_user_input(sys.argv)
run(user_input[0], user_input[1])
