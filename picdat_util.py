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
try:
    import pytz
except ImportError:
    pytz = None
    print('Warning: Module pytz is not installed. PicDat won\'t be able to convert '
          'timezones. Be aware of possible confusion with time values in charts!')

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
    (neither .data nor .zip nor .out nor .tgz nor .h5 nor .json).
    """
    if os.path.isdir(input_file):
        return
    elif not os.path.isfile(input_file):
        raise FileNotFoundError

    dtype = data_type(input_file)

    if dtype not in ['data', 'zip', 'out', 'tgz', 'h5', 'json']:
        raise TypeError


def take_input_file():
    """
    This function requests the location of a data file from the user.
    :return: The temporary directory's path (might be None, after usage of files inside this
    directory should become deleted) and a list of all PerfStat data files extracted from user
    input.
    """
    while True:
        input_file = input('Please enter a path to some performance output (folder or zipfolder '
                           'or .data or .out or .json file or .tgz archive):' + os.linesep)

        try:
            validate_input_file(input_file)
            return input_file
        except FileNotFoundError:
            print('This file does not exist. Try again.')
        except TypeError:
            print('Unexpected data type: File must be of type .data, .out, .zip, .json or .tgz. '
                  'Try again.')


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


def prepare_directory(destination_dir, compact_file):
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

    if not compact_file:
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
        opts, _ = getopt.getopt(argv[1:], 'hlscwd:i:o:',
            ['help', 'logfile', 'sortbynames', 'compact', 'webserver', 'debug=', 'input=', 'outputdir='])
        opts = dict(opts)
    except getopt.GetoptError:
        logging.exception('Couldn\'t read command line options.')
        print_help_and_exit(argv[0])

    # print help information if option 'help' is given
    if '-h' in opts or '--help' in opts:
        print_help_and_exit(argv[0])

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
    elif '--input' in opts:
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
        _ = [logging.root.removeHandler(handler) for handler in logging.root.handlers[:]]
        logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s', filename=output_dir
                            + os.sep + constants.LOGFILE_NAME, level=log_level)

    logging.info('inputfile: %s, outputdir: %s', os.path.abspath(input_file), os.path.abspath(
        output_dir))

    # Looks, whether user wants to sort legend entries alphabetically instead of by relevance
    sort_columns_by_name = ('-s' in opts or '--sortbynames' in opts)
    compact_file = ('-c' in opts or '--compact' in opts)
    webserver = ('-w' in opts or '--webserver' in opts)

    return input_file, output_dir, sort_columns_by_name, compact_file, webserver

def ccma_check(filenames):
    """
    Checks, if list of filenames contains files, which are characteristic of ccma ASUPs. This
    allows to explain the user, that PicDat needs those ASUPs to be preprocessed with Trafero.
    If it finds such files, quits the program.
    Should be called for filenames in a folder (possibly) containing an ASUP, which seems not
    to contain any other readable performance output.
    :param filenames: List of filenames which are suspected to include ccma archives.
    :returns: None
    """
    if 'PERFORMANCE-ARCHIVES.TAR' in filenames or any(
        [('CM-STATS-HOURLY-DATA-' in file and '.TAR' in file) for file in filenames]):
        logging.info('Seems like you gave some ASUP as input, which contains performance data not '
                     'in xml format, but in ccma files. PicDat can\'t read those files just like '
                     'that. Use Trafero to convert the ASUP into JSON first. Then pass the .json '
                     'files to PicDat.')
        sys.exit(0)

def extract_tgz(dir_path, tgz_file, data_name_extension=None):
    """
    Unpacks the 'CM-STATS-HOURLY-INFO.XML' and CM-STATS-HOURLY-DATA.XML' files from a tar file with
    file ending .tgz to a directory.
    :param dir_path: The directory's path, the files should become unpacked to.
    :param tgz_file: A tar files path.
    :param data_name_extension: As PicDat might want to unpack several data files into the same
    directory without overwriting each other, a unique name extension as string can be passed.
    :returns: The paths to the 'CM-STATS-HOURLY-INFO.XML', CM-STATS-HOURLY-DATA.XML' and 'HEADER'
    files inside the temporary directory dir_path.
    """
    asup_xml_info_file = constants.ASUP_INFO_FILE
    asup_data_file = constants.ASUP_DATA_FILE
    asup_xml_header_file = constants.ASUP_HEADER_FILE

    with tarfile.open(tgz_file, 'r') as tar:
        tarmembers = []
        try:
            tarmembers.append(tar.getmember(asup_xml_info_file))
            tarmembers.append(tar.getmember(asup_data_file))
            asup_xml_info_file = os.path.join(dir_path, asup_xml_info_file)
            asup_data_file = os.path.join(dir_path, asup_data_file)
        except KeyError:
            ccma_check(tar.getnames())
            logging.info(
                'PicDat needs CM-STATS-HOURLY-INFO.XML and CM-STATS-HOURLY-DATA.XML file. You '
                'gave a tgz archive which does not contain them. Quit program.')
            sys.exit(0)
        try:
            tarmembers.append(tar.getmember(asup_xml_header_file))
            asup_xml_header_file = os.path.join(dir_path, asup_xml_header_file)
        except KeyError:
            logging.info(
                'You gave a tgz archive without a HEADER file. This means, some meta data for '
                'charts are missing such as node and cluster name.')
            asup_xml_header_file = None

        tar.extractall(dir_path, members=tarmembers)

    if data_name_extension:
        os.rename(asup_data_file, asup_data_file + data_name_extension)
        asup_data_file = asup_data_file + data_name_extension

    return asup_xml_info_file, asup_data_file, asup_xml_header_file


def get_all_perfstats(folder):
    """
    Picks all .data files from a folder. Also picks a file named console.log, if available.
    Therefore, it ignores all sub folders named host.
    :param folder: A folder's path as String, which should be searched.
    :return: A tuple of a list of .data/.out files and the console.log file (might be None).
    """
    output_files = []
    perfstat_console_file = None
    for path, _, files in os.walk(folder):
        if 'host' in path:
            continue
        for filename in files:
            file = os.path.join(path, filename)
            if filename == 'console.log':
                perfstat_console_file = file
            elif data_type(filename) == 'data' or data_type(filename) == 'out':
                output_files.append(file)
    return output_files, perfstat_console_file


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

    output_files, perfstat_console_file = get_all_perfstats(temp_path)

    return temp_path, output_files, perfstat_console_file

def get_timezone(tz_string):
    """
    Creates a pytz.timezone object from a timezone String.
    Usually, the module pytz can handle such Strings by itself, but we face the problem that many
    files include the timezone string 'CEST' but pytz accepts only 'CET'; pytz wants to switch
    between summer time and winter time itself.
    This function simply translates 'CEST' to 'CET'. By appending to the tz_switch dict,
    translation could be done for other suspicious timezone strings as well.
    :param tz_string: A timezone identifier as String.
    :return: A pytz.timezone object, or None, if pytz throws an exception.
    """
    if not pytz:
        return None

    tz_switch = {
        'CEST': pytz.timezone('CET')
    }

    if tz_string in tz_switch:
        return tz_switch[tz_string]

    else:
        try:
            return pytz.timezone(tz_string)
        except pytz.UnknownTimeZoneError:
            logging.warning('Found unexpected timezone identifier: \'%s\'. '
                            'PicDat is not able to harmonize timezones. Be aware of possible '
                            'confusion with time values in charts.', tz_string)
            return None
