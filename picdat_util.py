"""
This modules contains several functions called by main module picdat. Therefore, they are for
handling user communication or directory work such as unpacking archives.
"""
import getopt
import logging
import os
import shutil
import sys
import tempfile
import tarfile
from zipfile import ZipFile
from general import constants

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


def data_type(filepath):
    """
    Gets a file's data type.
    :param filepath: The path from a file as String, you want to have the data type for.
    :return: The data type as String.
    """
    return filepath.split('.')[-1]


def get_log_level(log_level_string):
    """
    Turns a string into a log level, the logging module can understand
    :param log_level_string: A String representing a log level like 'info' or 'error'.
    :return: A constant from the logging module, representing a log level.
    """
    log_level_dict = {
        'debug': logging.DEBUG,
        'DEBUG': logging.DEBUG,
        'info': logging.INFO,
        'INFO': logging.INFO,
        'warning': logging.WARNING,
        'WARNING': logging.WARNING,
        'error': logging.ERROR,
        'ERROR': logging.ERROR,
        'critical': logging.CRITICAL,
        'CRITICAL': logging.CRITICAL
    }
    try:
        return log_level_dict[log_level_string]
    except KeyError:
        logging.error('No log level like \'%s\' exists. Try one of those: %s', log_level_string,
                      [entry for entry in log_level_dict])
        sys.exit(1)


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
    (neither .data nor .zip nor .out nor .tgz).
    """
    if os.path.isdir(input_file):
        return
    elif not os.path.isfile(input_file):
        raise FileNotFoundError

    dtype = data_type(input_file)

    if dtype not in ['data', 'zip', 'out', 'tgz']:
        raise TypeError


def take_input_file():
    """
    This function requests the location of a data file from the user.
    :return: The temporary directory's path (might be None, after usage of files inside this
    directory should become deleted) and a list of all PerfStat data files extracted from user
    input.
    """
    while True:
        input_file = input('Please enter a path to some PerfStat output (folder or zipfolder '
                           'or .data or .out file or .tgz archive):' + os.linesep)

        try:
            validate_input_file(input_file)
            return input_file
        except FileNotFoundError:
            print('This file does not exist. Try again.')
        except TypeError:
            print('Unexpected data type: File must be of type .data, .out, .zip, or .tgz. Try again.')


def take_directory():
    """
    This function requests a destination directory of the user. All results of the PicDat program
    will be written to this directory.
    :return: The path to the directory, the results should be written in
    """
    destination_directory = input('Please select a destination directory for the results ('
                                  'Default is ./results):' + os.linesep)
    if destination_directory == '':
        destination_directory = 'results'

    return destination_directory


def prepare_directory(destination_dir):
    """
    Copies the templates .jss and .css files into the given directory. Also creates an empty
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

    dygraphs_js_source = constants.DYGRAPHS_JS_SRC
    dygraphs_js_dest = dygraphs_dir + os.sep + 'dygraph.js'
    dygraphs_css_source = constants.DYGRAPHS_CSS_SRC
    dygraphs_css_dest = dygraphs_dir + os.sep + 'dygraph.css'
    shutil.copyfile(dygraphs_js_source, dygraphs_js_dest)
    shutil.copyfile(dygraphs_css_source, dygraphs_css_dest)

    return csv_dir


def handle_user_input(argv):
    """
    Processes command line options belonging to PicDat. If no log level is given, takes default
    log level instead. If no input file or output directory is given, PicDat will ask the user
    about them at runtime. If a log file is desired, logging content is redirected into picdat.log.
    :param argv: Command line parameters.
    :return: A tuple of two paths; the first one leads to the PerfStat input, the second one to
    the output directory.
    """

    # get all options from argv and turn them into a dict
    try:
        opts, _ = getopt.getopt(argv[1:], 'hsld:i:o:', ['help', 'sortbynames', 'logfile', 'debug=',
                                                        'inputfile=', 'outputdir='])
        opts = dict(opts)
    except getopt.GetoptError:
        logging.exception('Couldn\'t read command line options.')
        print_help_and_exit(argv[0])

    # print help information if option 'help' is given
    if '-h' in opts or '--help' in opts:
        print_help_and_exit(argv[0])

    # Looks, whether user wants to sort legend entries alphabetically instead of by relevance
    if '-s' in opts or '--sortbynames' in opts:
        sort_columns_by_name = True
    else:
        sort_columns_by_name = False

    # extract log level from options if possible
    if '-d' in opts:
        log_level = get_log_level(opts['-d'])
    elif '--debug' in opts:
        log_level = get_log_level(opts['--debug'])
    else:
        log_level = constants.DEFAULT_LOG_LEVEL

    logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s', level=log_level)

    # extract inputfile from options if possible
    if '-i' in opts:
        input_file = opts['-i']
    elif '--inputfile' in opts:
        input_file = opts['--inputfile']
    else:
        input_file = take_input_file()

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

    # decide, whether logging information should be written into a log file
    if '-l' in opts or '--logfile' in opts:
        [logging.root.removeHandler(handler) for handler in logging.root.handlers[:]]
        logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s', filename=output_dir
                            + os.sep + constants.LOGFILE_NAME, level=log_level)

    logging.info('inputfile: %s, outputdir: %s', os.path.abspath(input_file), os.path.abspath(
        output_dir))

    return input_file, output_dir, sort_columns_by_name


def extract_tgz(tgz_file):
    """
    Unpacks the 'CM-STATS-HOURLY-INFO.XML' and CM-STATS-HOURLY-DATA.XML' files from a tar file with
    file ending .tgz to a temporary directory.
    :param tgz_file: A tar files path.
    :returns: The path to the temporary directory, the files got unpacked into. It should become
    deleted with the stop of PicDat. Additionally, the paths to the 'CM-STATS-HOURLY-INFO.XML' and
    CM-STATS-HOURLY-DATA.XML' files inside the temporary directory.
    """
    temp_path = tempfile.mkdtemp()
    info_file = 'CM-STATS-HOURLY-INFO.XML'
    data_file = 'CM-STATS-HOURLY-DATA.XML'

    with tarfile.open(tgz_file, 'r') as tar:
        tar.extractall(temp_path, members=[tar.getmember(
            info_file), tar.getmember(data_file)])

    info_file = os.path.join(temp_path, info_file)
    data_file = os.path.join(temp_path, data_file)

    return temp_path, info_file, data_file

def get_all_perfstats(folder):
    """
    Pics all .data files from a folder. Also picks a file named console.log, if available.
    Therefore, it ignores all sub folders named host.
    :param folder: A folder's path as String, which should be searched.
    :return: A tuple of a list of .data/.out files and the console.log file (might be None).
    """
    output_files = []
    console_file = None
    for path, _, files in os.walk(folder):
        if 'host' in path:
            continue
        for filename in files:
            file = os.path.join(path, filename)
            if filename == 'console.log':
                console_file = file
            elif data_type(filename) == 'data' or data_type(filename) == 'out':
                output_files.append(file)
    return output_files, console_file


def extract_zip(zip_folder):
    """
    This function takes a zip folder, distracts it to a temporary directory and picks all .data
    files from it, but it ignores all files in folders named host. Also picks a file named
    console.log, if available.
    :param zip_folder: The path to a .zip file as String.
    :return: A tuple of the temporary directory's path, a list of all .output file paths,
    and the path to the console.log file (might be None).
    """
    temp_path = tempfile.mkdtemp()
    with ZipFile(zip_folder, 'r') as zip_file:
        zip_file.extractall(temp_path)

    output_files, console_file = get_all_perfstats(temp_path)

    return temp_path, output_files, console_file
