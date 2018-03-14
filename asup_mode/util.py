"""
This modules contains functions needed for the asup mode.
"""
import datetime
import logging

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


def get_abs_val(this_val, unixtimestamp, val_buffer, time_buffer, buffer_key):
    """
    As it seems that the counters storing the values written in the xml data file
    never get cleared, it is always necessary to calculate: (this_val -
    last_val)/(this_timestamp - last_timestamp) to get a useful, absolute value.
    This function does this calculation.
    :param this_val: the recent 'total' value
    :param unixtimestamp: the recent time stamp in unixtime format
    :param val_buffer: The buffer dict which stores the last 'total' value belonging to this_val
    :param time_buffer: The buffer dict which stores the last timestamp
    :param buffer_key: The request key which allocates the right places inside the buffers. It
    refers to the table and instance, the values belong to.
    """
    last_val = val_buffer[buffer_key]
    last_unixtime = time_buffer[buffer_key]
    abs_val = str((this_val - last_val) / (unixtimestamp - last_unixtime))
    datetimestamp = datetime.datetime.fromtimestamp(unixtimestamp)

    if unixtimestamp < last_unixtime:
        last_datetimestamp = datetime.datetime.fromtimestamp(last_unixtime)
        logging.warning('PicDat read two values in wrong chronological order (Timestamps %s and '
                        ' %s). This is probably because PicDat sorts its input files '
                        'alphabetically. This will cause problems if the alphabetical order of '
                        'filenames is not equivalent to the chronological order of the content. '
                        'So, you probably gave several .tgz files as input, which names do not '
                        'contain a time stamp or anything, which secures the order. Be aware that '
                        'there will be falsifications in charts at the margins of data from '
                        'different files!', last_datetimestamp, datetimestamp)

    logging.debug('(recent_val - last_val)/(recent_time - last_time) = (%s - %s)/(%s - %s) = '
                  '%s (%s)', this_val, last_val, unixtimestamp, last_unixtime, abs_val, buffer_key)

    return abs_val, datetimestamp
