"""
This modules contains functions needed for the asup mode.
"""
import datetime
import logging
import sys

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


def get_abs_val(this_val, unixtimestamp, val_buffer, buffer_key):
    """
    As it seems that the counters storing the values written in the xml data file
    never get cleared, it is always necessary to calculate: (this_val -
    last_val)/(this_timestamp - last_timestamp) to get a useful, absolute value.
    This function does this calculation.
    :param this_val: the recent 'total' value
    :param unixtimestamp: the recent time stamp in unixtime format
    :param val_buffer: The buffer dict which stores the last 'total' value belonging to this_val
    :param buffer_key: The request key which allocates the right places inside the buffers. It
    refers to the table and instance, the values belong to.
    """
    last_unixtime = val_buffer[buffer_key][0]
    last_val = val_buffer[buffer_key][1]

    if isinstance(this_val, list):
        abs_val = [str((float(this_val[i]) - float(last_val[i])) /
                       (unixtimestamp - last_unixtime)) for i in range(len(this_val))]
    else:
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


def get_flat_tables(asup_container, sort_columns_by_name):
    """
    Calls the flatten method for each table from asup_container.tables, which is not empty.
    :param asup_container: xml_container, json_container, or hdf5_container object. Those container
    object does have a similar structure, so their tables can be flattened in the same way by this
    function.
    :param sort_columns_by_name: boolean, whether table columns should be sorted
    by names. If False, they will be sorted by value. Tables for
    COUNTERS_OVER_TIME_KEYS will always be sorted by names, because this is considered
    to be a clearer arrangement.
    :return: all not-empty flattened tables in a list.
    """

    # get the three key list INSTANCES_OVER_TIME_KEYS, INSTANCES_OVER_BUCKET_KEYS, and
    # COUNTERS_OVER_TIME_KEYS. Each asup container's module has this key lists, but they may vary a
    # bit, so it is important to access the keys over the given container object.
    instances_over_time_keys = sys.modules[asup_container.__module__].INSTANCES_OVER_TIME_KEYS
    instances_over_bucket_keys = sys.modules[asup_container.__module__].INSTANCES_OVER_BUCKET_KEYS
    counters_over_time_keys = sys.modules[asup_container.__module__].COUNTERS_OVER_TIME_KEYS

    # initialise table list
    flat_tables = []

    flat_tables = flat_tables + [asup_container.tables[key].flatten('time', sort_columns_by_name)
                                 for key in instances_over_time_keys
                                 if not asup_container.tables[key].is_empty()]

    flat_tables = flat_tables + [asup_container.tables[key].flatten('bucket', sort_columns_by_name)
                                 for key in instances_over_bucket_keys
                                 if not asup_container.tables[key].is_empty()]

    flat_tables = flat_tables + [asup_container.tables[key_id].flatten('time', True)
                                 for (key_id, _, _) in counters_over_time_keys
                                 if not asup_container.tables[key_id].is_empty()]
    return flat_tables


def build_label_dict(asup_container):
    """
    This method provides meta information about the data found in the ASUPs. Those are the charts
    identifiers (tuple of two strings, unique for each chart, used for chart titles, file names
    etc), units, and one boolean for each chart, which says, whether the chart is a histogram
    (histograms are visualized differently; their x-axis is not 'time' but 'bucket' and they
    are plotted as bar charts).
    :param asup_container: xml_container, json_container, or hdf5_container object. Those container
    object does have a similar structure, so their labels can be gathered in the same way by this
    function.
    :return: all mentioned information, packed into a dict
    """

    # get the three key list INSTANCES_OVER_TIME_KEYS, INSTANCES_OVER_BUCKET_KEYS, and
    # COUNTERS_OVER_TIME_KEYS. Each asup container's module has this key lists, but they may vary a
    # bit, so it is important to access the keys over the given container object.
    instances_over_time_keys = sys.modules[asup_container.__module__].INSTANCES_OVER_TIME_KEYS
    instances_over_bucket_keys = sys.modules[asup_container.__module__].INSTANCES_OVER_BUCKET_KEYS
    counters_over_time_keys = sys.modules[asup_container.__module__].COUNTERS_OVER_TIME_KEYS

    # initialise label lists
    identifiers = []
    units = []
    is_histo = []

    # get labels for all charts belonging to INSTANCES_OVER_TIME_KEYS
    available = [
        key for key in instances_over_time_keys if not asup_container.tables[key].is_empty()]

    identifiers += available
    units += [asup_container.units[key] for key in available]
    is_histo += [False for _ in available]

    # get labels for all charts belonging to INSTANCE_OVER_BUCKET_KEYS
    available = [
        key for key in instances_over_bucket_keys if not asup_container.tables[key].is_empty()]

    identifiers += available
    units += [asup_container.units[key] for key in available]
    is_histo += [True for _ in available]

    # get labels for all charts belonging to COUNTERS_OVER_TIME_KEYS
    available = [(key_object, key_id) for (key_id, key_object, _) in counters_over_time_keys
                 if not asup_container.tables[key_id].is_empty()]

    identifiers += [(key_object.replace('system:constituent', asup_container.node_name
                                        ).replace('system', asup_container.node_name),
                     key_id) for (key_object, key_id) in available]
    units += [asup_container.units[key_id] for (_, key_id) in available]
    is_histo += [False for _ in available]

    return {'identifiers': identifiers, 'units': units, 'is_histo': is_histo}
