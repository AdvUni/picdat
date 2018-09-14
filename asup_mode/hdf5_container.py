"""
Contains the class Hdf5Container. This class is responsible for holding and
processing all data collected from a hdf5 file.
"""
import logging
import math
import datetime
from collections import defaultdict
from general.table import Table

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


# The following three lists contain search keys for gaining chart data. Each element of the lists
# is a key to collect data for exactly one chart. As there are three different kinds of charts, the
# keys are partitioned into the different lists.

# Each element of the INSTANCES_OVER_TIME_KEYS list is a pair of an object and a counter, as they
# are written into the ASUP hdf5 files. Several instances of the object will have data for the
# counter, so the resulting chart for each of the keys will have one data series per instance.
# The x axis of the charts will be 'time'. These two characteristics makes the keys different from
# the keys in the other lists, so this is why the list is called like this.

INSTANCES_OVER_TIME_KEYS = [('aggregate', 'total_transfers'),
                            ('ext_cache_obj', 'hya_reads_replaced'),
                            ('processor', 'processor_busy'), ('disk', 'disk_busy'),
                            ('volume', 'total_ops'), ('volume', 'avg_latency'),
                            ('volume', 'read_data'), ('volume', 'write_data'),
                            ('lun', 'total_ops'), ('lun', 'avg_latency'), ('lun', 'read_data')]

# The following list contains search keys about histograms.
# Each element of the INSTANCES_OVER_BUCKET_KEYS list is a pair of an object and a counter, as they
# are written into the ASUP hdf5 files. Several instances of the object will have data for the
# counter, so the resulting chart for each of the keys will have one data series per instance.
# As it is hardly useful, to draw a histogram as time diagram, the x axis will not be 'time', but
# 'bucket' here. These two characteristics makes the keys different from the keys in the other
# lists, so this is why the list is called like this.
INSTANCES_OVER_BUCKET_KEYS = [('lun', 'read_align_histo')]

# Each element of the COUNTERS_OVER_TIME_KEYS list is a triple of an identifier, an object and a
# set of counters. Objects and counters are some of those written into the ASUP hdf5 files.
# The identifier is just for distinction between several keys of the list, because the objects are
# not unique and the counter sets are not very handy. The identifier is used for referencing the
# data belonging to the key at runtime as well as for naming the resulting charts and must be
# unique.
# For the objects of those keys, it is assumed, that each hdf5 data file knows only one instance per
# object. So, each chart belonging to the keys is not meant to have several data series for
# different instances, but data series for different counters instead. This is why each key
# contains a whole set of counters. The counters in one set must of course wear all the same unit!
# The x axis of the charts will be 'time'. These two characteristics makes the keys different from
# the keys in the other lists, so this is why the list is called like this.
COUNTERS_OVER_TIME_KEYS = [
    ('bandwidth', 'system', {'hdd_data_read', 'hdd_data_written', 'net_data_recv',
                             'net_data_sent', 'ssd_data_read', 'ssd_data_written',
                             'fcp_data_recv', 'fcp_data_sent', 'tape_data_read',
                             'tape_data_written'}),
    ('IOPS', 'system', {'nfs_ops', 'cifs_ops', 'fcp_ops', 'iscsi_ops', 'other_ops'}),
    ('fragmentation', 'raid', {'partial_stripes', 'full_stripes'})
]


class Hdf5Container:
    """
    This class is responsible for holding and processing all data collected from hdf5 files. It
    takes hdf5 tables and saves their contents into table objects of type general.Tables, if they
    match the search keys.
    Furthermore, it provides meta data like table names and axis labeling information.
    """

    def __init__(self):
        """
        Constructor for Hdf5Container.
        """

        # A dict of Table objects. Each key from the three key lists has exactly one Table
        # storing all the matching data found in hdf5 data file.
        self.tables = {searchkey: Table()
                       for searchkey in INSTANCES_OVER_TIME_KEYS + INSTANCES_OVER_BUCKET_KEYS}
        for key_id, _, _ in COUNTERS_OVER_TIME_KEYS:
            self.tables[key_id] = Table()

        # A dict for relating units to each search key from the three key lists.
        # Units are provided by the hdf5 info file.
        self.units = {}

        # Histograms are charts with an x label different from 'time'. Which x values can occur is
        # precisely specified in the info file within the tag 'label1'.
        self.histo_labels = {}

        # The following dict is for storing the information from hdf5 base tags in the info file.
        # Its keys are tuples specifying object and the counter name of a base, its values are
        # the respective counters, to which the base belongs to.
        # Note: It is assumed, that values belonging to COUNTERS_OVER_TIME_KEYS do not have any
        # bases. So, those dicts do only work for the INSTANCES_OVER_TIME_KEYS
        self.base_dict = {}
        # Same thing as base_dict, but it stores the bases for INSTANCES_OVER_BUCKET_KEYS instead.
        self.histo_base_dict = {}

        # In case some base elements appear in hdf5 before the elements, they are the base to, they
        # will be thrown into this set to process them later.
        self.base_heap = set()

        # To get a nice title for the last system chart, the program reads the node name from one
        # of the hdf5 elements. This node name will substitute the word 'system' in chart labels.
        self.node_name = None

        self.units = {searchkey: 'nix' for searchkey in INSTANCES_OVER_TIME_KEYS +
                      INSTANCES_OVER_BUCKET_KEYS}
        for key_id, _, _ in COUNTERS_OVER_TIME_KEYS:
            self.units[key_id] = 'nix'

    def process_buffer(self, buffer, table_key):
        """
        To secure the chronological order among the rows from one hdf5 table, all relevant data
        is collected into a buffer. When all data is collected, the buffer gets sorted before
        converting the values and storing them to self.tables. This method does this actions for
        a given buffer.
        :param buffer: A dict, storing all relevant data from one hdf5 table. Its keys are the
        columns of the general.Table() objects from self.tables, the values belong to (Can either
        be instance names or counter names, respective to the KEYS, the buffer belong to). The
        values of the buffer dict are lists of tuples of a unixtimestamp and the value. So, the
        structure is like this: buffer = {column_name: [(row_name, value), (row_name, value)...}
        """
        for buffer_key, buffer_tuple in buffer.items():
            last_unixtimestamp = None
            last_value = None
            for unixtimestamp, value in sorted(buffer_tuple):
                if last_unixtimestamp:
                    abs_value = str((value - last_value) / (unixtimestamp - last_unixtimestamp))
                    datetimestamp = datetime.datetime.fromtimestamp(unixtimestamp)
                    self.tables[table_key].insert(datetimestamp, buffer_key, abs_value)
                last_unixtimestamp = unixtimestamp
                last_value = value

    def search_hdf5(self, hdf5_table):
        """
        Method takes a hdf5 table and checks, whether it refers to an object type from
        INSTANCES_OVER_TIME_KEYS or COUNTERS_OVER_TIME_KEYS. If so, it selects all rows from it,
        which belong to a counter specified in a key. From this rows, it collects the necessary
        information and converts the value to get the absolute value and not only the recent total
        value of the counter, as it is written in the hdf5 file. Finally it stores the value to the
        respective table in self.tables.
        :param hdf5 table: a pytable's Table object
        :return: None
        """
        object_type = hdf5_table.name

        # process INSTANCES_OVER_TIME_KEYS
        for key_object, key_counter in INSTANCES_OVER_TIME_KEYS:
            if object_type == key_object:
                buffer = defaultdict(set)
                for row in hdf5_table.where('counter_name == key_counter'):
                    unixtimestamp = int(row['timestamp'])
                    unixtimestamp = math.trunc(unixtimestamp / 1000)
                    instance = str(row['instance_name']).strip('b\'').replace(',', ';')
                    value = float(row['value_int'])
                    buffer[instance].add((unixtimestamp, value))

                    logging.debug('object: %s, counter: %s, time: %s, instance: %s, value: %s',
                                  object_type, key_counter, unixtimestamp, instance, value)

                self.process_buffer(buffer, (object_type, key_counter))

        # process INSTANCE_OVER_BUCKET_KEYS
        for key_object, key_counter in INSTANCES_OVER_BUCKET_KEYS:
            if object_type == key_object:
                histo_buffer = {}
                for row in hdf5_table.where('counter_name == key_counter'):
                    unixtimestamp = int(row['timestamp'])
                    unixtimestamp = math.trunc(unixtimestamp / 1000)
                    instance = str(row['instance_name']).strip('b\'').replace(',', ';')
                    value = float(row['value_int'])
                    bucket = str(row['x_label']).strip('b\'')

                    if (bucket, instance) in histo_buffer:
                        if histo_buffer[bucket, instance]:
                            last_unixtimestamp, last_value = histo_buffer[bucket, instance]
                            abs_value = str((value - last_value) /
                                            (unixtimestamp - last_unixtimestamp))
                            self.tables[object_type, key_counter].insert(
                                bucket, instance, str(abs_value))
                            histo_buffer[bucket, instance] = None

                    else:
                        histo_buffer[bucket, instance] = unixtimestamp, value

        # Process COUNTERS_OVER_TIME_KEYS
        for key_id, key_object, key_counters in COUNTERS_OVER_TIME_KEYS:
            if object_type == key_object:
                buffer = defaultdict(set)
                for key_counter in key_counters:
                    for row in hdf5_table.where('counter_name == key_counter'):

                        unixtimestamp = int(row['timestamp'])
                        unixtimestamp = math.trunc(unixtimestamp / 1000)
                        value = float(row['value_int'])
                        buffer[key_counter].add((unixtimestamp, value))

                        logging.debug('object: %s, counter: %s, time: %s, value: %s',
                                      object_type, key_counter, unixtimestamp, value)

                        # collect node name once
                        if not self.node_name:
                            if object_type == 'system':
                                self.node_name = str(row['instance_name']).strip('b\'')
                                logging.debug('found node name: %s', self.node_name)

                self.process_buffer(buffer, key_id)

    def do_unit_conversions(self):  # not used
        """
        This method improves the presentation of some values through unit conversion. Don't call it
        before all data files are read!
        :return: None
        """
        for unit_key, unit in self.units.items():
            if unit == 'percent':
                self.tables[unit_key].expand_values(100)
                self.units[unit_key] = '%'

            if unit == "b_per_sec":
                self.tables[unit_key].expand_values(1 / (10**6))
                self.units[unit_key] = "Mb/s"

            if unit == 'kb_per_sec':
                self.tables[unit_key].expand_values(1 / (10**3))
                self.units[unit_key] = "Mb/s"
