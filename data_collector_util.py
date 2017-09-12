"""
Small util module with functions only used by the data collector module.
"""
import util
import datetime

try:
    import pytz
except ImportError:
    pytz = None
    print('''
Warning: module pytz is not installed. PicDat won't be able to convert timezones.
Be aware of possible confusion with time values in charts.
''')

import global_vars

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
    month = util.get_month_number(timestamp_list[1])
    day = int(timestamp_list[2])
    time = timestamp_list[3].split(":")
    if pytz is not None:
        timezone = util.get_timezone(timestamp_list[4])
    else:
        timezone = None
    year = int(timestamp_list[5])

    hour = int(time[0])
    minute = int(time[1])
    second = int(time[2])

    # check, whether global variable 'localetimezone' is already set
    if global_vars.localtimezone is None:
        global_vars.localtimezone = timezone

    # convert timezone to global_vars.localtimezone (as possible) and return datetime object
    try:
        return timezone.localize(
            datetime.datetime(year, month, day, hour, minute, second, 0, None)).astimezone(
            global_vars.localtimezone).replace(tzinfo=None)
    except (AttributeError, TypeError):
        global_vars.localtimezone = '???'
        return datetime.datetime(year, month, day, hour, minute, second, 0, None)


def get_iteration_timestamp(iteration_timestamp_line):
    """
    Extract a date from a PerfStat output line which marks an iteration's beginning or ending
    :param iteration_timestamp_line: a string like
    =-=-=-=-=-= BEGIN Iteration 1  =-=-=-=-=-= Mon Jan 01 00:00:00 GMT 2000
    :return: a datetime object which contains the input's time information
    """
    return build_date(iteration_timestamp_line.split('=-=-=-=-=-=')[2])


def get_sysstat_timestamp(sysstat_timestamp_line):
    """
    Extract a date from a PerfStat output line which contains the time, a sysstat_x_1sec block
    begins.
    :param sysstat_timestamp_line: a string like
    PERFSTAT_EPOCH: 0000000000 [Mon Jan 01 00:00:00 GMT 2000]
    :return: a datetime object which contains the input's time information
    """
    return build_date(sysstat_timestamp_line.split('[')[1].replace(']', ''))


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
        print('Planned number of iterations was executed correctly.')
    elif expected_iteration_number != iteration_beginnings:
        print('''
        Warning: PerfStat output is incomplete; some iterations weren't executed.
        If there is an iteration which wasn't finished correctly, it won't be considered in the 
        resulting charts!
        ''')
    else:
        print('''
        Warning: PerfStat output is incomplete; the last iteration didn't terminate.
        It won't be considered in the resulting charts!
        ''')
