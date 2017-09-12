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


def get_iteration_timestamp(iteration_timestamp_line):
    """
    Extract a date from a PerfStat output line which marks an iteration's beginning or ending
    :param iteration_timestamp_line: a string like
    =-=-=-=-=-= BEGIN Iteration 1  =-=-=-=-=-= Mon Jan 01 00:00:00 GMT 2000
    :return: a datetime object which contains the input's time information
    """
    return util.build_date(iteration_timestamp_line.split('=-=-=-=-=-=')[2])


def get_sysstat_timestamp(sysstat_timestamp_line):
    """
    Extract a date from a PerfStat output line which contains the time, a sysstat_x_1sec block
    begins.
    :param sysstat_timestamp_line: a string like
    PERFSTAT_EPOCH: 0000000000 [Mon Jan 01 00:00:00 GMT 2000]
    :return: a datetime object which contains the input's time information
    """
    return util.build_date(sysstat_timestamp_line.split('[')[1].replace(']', ''))


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
