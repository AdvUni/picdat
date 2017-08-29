"""
Small util module with functions only used by the data collector module.
"""
import util
import datetime

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


def build_date(iteration_timestamp):
    """
    extract a date from a PerfStat output line which marks an iteration's begining or ending
    :param iteration_timestamp: a string like
    =-=-=-=-=-= BEGIN Iteration 1  =-=-=-=-=-= Fri Mar 24 09:42:59 CET 2017
    :return: a datetime object which contains the input's information
    """
    timestamp_list = iteration_timestamp.split()

    month = util.get_month_number(timestamp_list[6])
    day = int(timestamp_list[7])
    time = timestamp_list[8].split(":")
    # time_zone = (header_list[9])
    year = int(timestamp_list[10])

    hour = int(time[0])
    minute = int(time[1])
    second = int(time[2])

    return datetime.datetime(year, month, day, hour, minute, second, 0, None)


def final_iteration_validation(expected_iteration_number, iteration_beginnings, iteration_endings):
    """
    test whether the PerfStat test terminated and is complete
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
        If there is an iteration, which wasn't finished correctly, it won't be considered in the 
        resulting charts!
        ''')
    else:
        print('''
        Warning: PerfStat output is incomplete; the last iteration didn't terminate.
        It won't be considered in the resulting charts!
        ''')
