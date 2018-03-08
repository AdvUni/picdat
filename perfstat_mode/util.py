"""
Provides some functions other modules inside package perfstat_mode may use.
"""
import logging
import datetime
import sys
try:
    import pytz
except ImportError:
    pytz = None
    print('Warning: Module pytz is not installed. PicDat won\'t be able to convert '
          'timezones. Be aware of possible confusion with time values in charts!')

from general.table import Table
from general import constants

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

# PerfStat output might be somewhat inconsistent in dealing with timezones. Therefore,
# PicDat wants to convert all time information into local time. As local timezone, it takes the
# first timezone it finds in the PerfStat file. Note: this is a global var. Global vars are
# usually not the best practise, but I wanted to avoid passing it as argument all the time. So
# make sure to clear this value before you handling a new PerfStat file!
localtimezone = None


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


def get_month_number(month_string):
    """
    Find the corresponding month number to a simple month string
    :param month_string: String describing a month's shortcut, three letters long, first letter
    upper case.
    :return: The corresponding month number
    """
    return {
        'Jan': 1,
        'Feb': 2,
        'Mar': 3,
        'Apr': 4,
        'May': 5,
        'Jun': 6,
        'Jul': 7,
        'Aug': 8,
        'Sep': 9,
        'Oct': 10,
        'Nov': 11,
        'Dec': 12
    }[month_string]


def get_timezone(tz_string):
    """
    Creates a pytz.timezone object from a timezone String as it appears in a PerfStat file.
    Usually, the module pytz can handle such Strings by itself, but some timezone identifiers
    need translation. (For example, CEST is no real timezone but the summer equivalent of CET,
    and pytz wants to handle it as CET.)
    :param tz_string: A timezone identifier from a PerfStat file as String.
    :return: A pytz.timezone object.
    """

    tz_switch = {
        'CEST': pytz.timezone('CET')
    }

    if tz_string in tz_switch:
        return tz_switch[tz_string]

    else:
        try:
            return pytz.timezone(tz_string)
        except pytz.UnknownTimeZoneError:
            logging.warning('Found unexpected timezone identifier in PerfStat file: \'%s\'. '
                            'PicDat is not able to harmonize timezones. Be aware of possible '
                            'confusion with time values in charts.', tz_string)
            return '???'


def build_date(timestamp_string):
    """
    Auxiliary function for get_iteration_timestamp and get_sysstat_timestamp. Parses a String to
    a datetime object and converts it into UTC.
    :param timestamp_string: a string like
    Mon Jan 01 00:00:00 GMT 2000
    :return: a datetime object which contains the input's information converted to UTC timezone.
    """

    timestamp_list = timestamp_string.split()

    # collect all information needed to create a datetime object from timestamp_string
    month = get_month_number(timestamp_list[1])
    day = int(timestamp_list[2])
    time = timestamp_list[3].split(":")
    if pytz is not None:
        timezone = get_timezone(timestamp_list[4])
    else:
        timezone = None
    year = int(timestamp_list[5])

    hour = int(time[0])
    minute = int(time[1])
    second = int(time[2])

    # check, whether global variable 'localtimezone' is already set
    global localtimezone
    if localtimezone is None:
        localtimezone = timezone

    # convert timezone to global_vars.localtimezone (as possible) and return datetime object
    try:
        return timezone.localize(
            datetime.datetime(year, month, day, hour, minute, second, 0, None)).astimezone(
                localtimezone).replace(tzinfo=None)
    except (AttributeError, TypeError):
        localtimezone = '???'
        return datetime.datetime(year, month, day, hour, minute, second, 0, None)


def check_column_header(word_upper_line, endpoint_upper_word, lower_line, request_upper_string,
                        request_lower_string):
    """
    This function helps checking, whether a column name in a pure text file, which is split over
    two lines, matches the request. Example: There is a text-based table with following headers:

    Disk   kB/s   Disk   OTHER    FCP  iSCSI     FCP   kB/s   iSCSI   kB/s
    read  write   util                            in    out      in    out

    You are looking for the 'Disk util' column. Therefore, you need to consider both lines. This
    function takes a word from the first line, compares it to a request, you would expect in the
    first line as well (Here: 'Disk') and finally compares the word in the second line right
    under the other word (for this it needs the parameter 'endpoint_upper_word' with the request
    word, you would expect in the second line (Here: 'util').
    :param word_upper_line: A word from the first header line
    :param endpoint_upper_word: The line index, the previous word ends
    :param lower_line: The whole second header line
    :param request_upper_string: Word from request you are looking for, expected in the upper line
    :param request_lower_string: Word from request you are looking for, expected in the lower line
    :return: True, if the word_upper_line you gave in belongs to the request you gave in and
    False otherwise.
    """
    if word_upper_line == request_upper_string:
        end = endpoint_upper_word
        start = end - len(request_lower_string)

        return request_lower_string == lower_line[start:end]
    else:
        return False


def inner_set_insertion(outer_list, index, item):
    """
    Inserts an item into a list of Sets. Inserts the item in the Set at the place of
    index. Is index bigger than the number of existing Sets, new Sets inside the
    list will be created.
    :param outer_list: The list of Sets you want to insert an item in.
    :param index: The Set's number, in which the item should be inserted in.
    :param item: The item you want insert.
    :return: None
    """
    if len(outer_list) <= index:
        missing_entries = index + 1 - len(outer_list)
        for _ in range(missing_entries):
            outer_list.append(set())

    outer_list[index].add(item)


def tablelist_insertion(tablelist, list_index, iteration, instance, item):
    """
    Inserts a table item into a specific table in a list of tables. If the list index is bigger
    than the number of table elements in the list, table elements will be created.
    :param tablelist: A list of tables. The function will insert the item in one of those.
    :param list_index: The table's index in tablelist, you want to insert your item in.
    :param iteration: The number of iteration, your item belongs to - is needed to arrange
    elements inside one table.
    :param instance: The name as string of the instance, your item (which should be a value for
    this instance) belongs to - is needed to arrange elements inside one table.
    :param item: The table value you want to insert. It's related to a specific time and object
    instance, therefore it is the basis for a single measuring point in final charts.
    """
    if len(tablelist) <= list_index:
        missing_entries = list_index + 1 - len(tablelist)
        for _ in range(missing_entries):
            tablelist.append(Table())

    tablelist[list_index].insert(iteration, instance, item)


def check_tablelist_content(tablelist, total_size):
    """
    This function checks, whether a table list contains content at each expected position. It
    generates a further list, which holds a boolean for each table list entry. It says False for
    each empty table and True, otherwise. If the table list isn't even fully built, means if it is
    shorter than expected, the function will append False entries to the availability list
    respectively.
    :param tablelist: A list of type Table.
    :param total_size: The total number of elements, tablelist should hold, if it would be fully
    filled.
    :return: An availability list of size total_size containing booleans.
    """
    availability_list = [not table.is_empty() for table in tablelist]
    while len(availability_list) < total_size:
        availability_list.append(False)
    return availability_list


def get_csv_filenames(object_ids, output_identifier):
    """
    Generates proper names for CSV files containing a selection of PerfStat Data.
    :return: A list of csv file names.
    :param request_objects: A list of all used request objects (necessary to get meta data about
    the tables)
    """
    name_list = []

    for object_id in object_ids:
        name_list.append(output_identifier + object_id + constants.CSV_FILE_ENDING)

    logging.debug('csv names: %s', name_list)
    return name_list


def read_console_file(perfstat_console_file):
    """
    Reads some information from a console.log file as it is attached to PerfStat output.data files.
    :param perfstat_console_file: A console.log file from a PerfStat output bundle.
    :return: A Dict, mapping the PerfStats node addresses to tuples of their
    cluster and node names.
    """
    with open(perfstat_console_file, 'r') as log:

        line = ''
        while not line.startswith('Vserver'):
            line = next(log)

        next(log)
        inside_block = True
        cluster = None
        identifier_dict = {}

        while inside_block:
            line = next(log)
            line_split = line.split()

            if len(line_split) == 0 or 'entries were displayed' in line:
                inside_block = False
            elif len(line_split) == 1:
                cluster = line_split[0]
            else:
                adress = line_split[2].split('/')[0]
                node = line_split[3]

                identifier_dict[adress] = (cluster, node)

        logging.debug('dict with cluster and node: ' + str(identifier_dict))

        return identifier_dict


def get_html_title(identifier_dict, perfstat_adress):
    """
    Generates a nice title for writing into the html file, based on cluster and node name of
    recent PerfStat.
    :param identifier_dict: A Dict, mapping the PerfStats node addresses to tuples of their
    cluster and node names.
    :param perfstat_adress: The node adress of the recent PerfStat (like it is used in PerfStat
    directory names)
    :return: A String, containing cluster and node information about a PerfStat.
    """
    cluster, node = identifier_dict[perfstat_adress]
    return 'Cluster: ' + cluster + '&ensp; &ensp; Node: ' + node


def empty_line(value_list):
    """
    Generates an empty data line for a value list. This is for interrupting the
    templates graph lines in resulting charts. Therefore, this line should be inserted between
    iterations.
    :param value_list: the list you want to add an empty line to.
    :return: A list of empty Strings in the length of value_list.
    """
    if len(value_list) != 0 and value_list[0] is not None:
        columns = len(value_list[0])
        return [' ' for _ in range(columns + 1)]
