"""
Contains the class JsonContainer. This class is responsible for holding and
processing all data collected from json files.
"""
import logging
import datetime
import math
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
# are written into ASUP json objects provided by trafero. Several instances of the object will
# have data for the counter, so the resulting chart for each of the keys will have one data series
# per instance. The x axis of the charts will be 'time'. These two characteristics makes the keys
# different from the keys in the other lists, so this is why the list is called like this.
INSTANCES_OVER_TIME_KEYS = [('aggregate', 'total_transfers'),
                            ('ext_cache_obj', 'hya_reads_replaced'),
                            ('processor', 'processor_busy'), ('disk', 'disk_busy'),
                            ('volume', 'total_ops'), ('volume', 'avg_latency'),
                            ('volume', 'read_data'), ('volume', 'write_data'),
                            ('lun', 'total_ops'), ('lun', 'avg_latency'), ('lun', 'read_data')]

# The following list contains search keys about histograms.
# Each element of the INSTANCES_OVER_BUCKET_KEYS list is a pair of an object and a counter, as they
# are written into json objects provided by trafero. Several instances of the object will have data
# for the counter, so the resulting chart for each of the keys will have one data series per
# instance. As it is hardly useful, to draw a histogram as time diagram, the x axis will not be
# 'time', but 'bucket' here. These two characteristics makes the keys different from the keys in
# the other lists, so this is why the list is called like this.
INSTANCES_OVER_BUCKET_KEYS = [('lun', 'read_align_histo')]

# Each element of the COUNTERS_OVER_TIME_KEYS list is a triple of an identifier, an object and a
# set of counters. Objects and counters are some of those written into json objects provided by
# trafero.
# The identifier is just for distinction between several keys of the list, because the objects are
# not unique and the counter sets are not very handy. So the identifier could be just any word.
# The identifier is used for referencing the data belonging to the key at runtime as well as for
# naming the resulting charts and must be unique.
# For the objects of those keys, it is assumed, that each JSON file knows only one instance per
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


class JsonContainer:
    """
    This class is responsible for holding and processing all data collected from json files. It
    takes json objects as dicts and saves their information into tables, if they match the search
    keys.
    Furthermore, it provides meta data like table names and axis labeling information.
    """

    def __init__(self):
        """
        Constructor for JsonContainer.
        """

        # A dict of Table objects. Each key from the three key lists has exactly one Table
        # storing all the matching data found in hdf5 data file.
        self.tables = {searchkey: Table()
                       for searchkey in INSTANCES_OVER_TIME_KEYS + INSTANCES_OVER_BUCKET_KEYS}
        for key_id, _, _ in COUNTERS_OVER_TIME_KEYS:
            self.tables[key_id] = Table()

        # To get a nice title for the last system chart, the program reads the node name from one
        # of the json objects. This node name will substitute the word 'system' in chart labels.
        self.node_name = None

        # A dict for relating units to each search key from the three key lists. None values will
        # be replaced while reading the data
        self.units = {}
        self.units = {searchkey: None for searchkey in INSTANCES_OVER_TIME_KEYS +
                      INSTANCES_OVER_BUCKET_KEYS}
        for key_id, _, _ in COUNTERS_OVER_TIME_KEYS:
            self.units[key_id] = None

    def add_data(self, json_item):
        """
        Method takes a dict, which contains the contents of a json object. Each of those dicts
        should contain one value together with all information what the value is about.
        If the dict matches a search key, its data will be written into table data structures.
        Method collects also units for the provided values.
        :param json_item: A dict representing a json object.
        :return: None
        """

        try:

            object_type = json_item['object_name']

            # process INSTANCES_OVER_TIME_KEYS
            for key_object, key_counter in INSTANCES_OVER_TIME_KEYS:
                if object_type == key_object:
                    if json_item['counter_name'] == key_counter:
                        timestamp = datetime.datetime.fromtimestamp(
                            math.trunc(json_item['timestamp'] / 1000))
                        instance = json_item['instance_name']
                        value = str(json_item['counter_value'])
                        logging.debug('object: %s, counter: %s, time: %s, instance: %s, value: %s',
                                      key_object, key_counter, timestamp, instance, value)

                        self.tables[key_object, key_counter].insert(timestamp, instance, value)

                        if not self.units[key_object, key_counter]:
                            self.units[key_object, key_counter] = json_item['counter_unit']
                        break

            # process INSTANCE_OVER_BUCKET_KEYS
            for key_object, key_counter in INSTANCES_OVER_BUCKET_KEYS:
                if object_type == key_object:
                    if json_item['counter_name'] == key_counter:
                        bucket = json_item['x_label']
                        instance = json_item['instance_name']
                        value = str(json_item['counter_value'])
                        logging.debug(
                            'object: %s, counter: %s, bucket: %s, instance: %s, value: %s',
                            key_object, key_counter, bucket, instance, value)

                        self.tables[key_object, key_counter].insert(bucket, instance, value)

                        if not self.units[key_object, key_counter]:
                            self.units[key_object, key_counter] = json_item['counter_unit']
                        break

            # Process COUNTERS_OVER_TIME_KEYS
            for key_id, key_object, key_counters in COUNTERS_OVER_TIME_KEYS:
                if object_type == key_object:
                    counter = json_item['counter_name']
                    for key_counter in key_counters:
                        if counter == key_counter:
                            timestamp = datetime.datetime.fromtimestamp(
                                math.trunc(json_item['timestamp'] / 1000))
                            value = str(json_item['counter_value'])
                            logging.debug('object: %s, counter: %s, time: %s, value: %s',
                                          key_object, key_counter, timestamp, value)

                            self.tables[key_id].insert(timestamp, counter, value)

                            # collect node name once
                            if not self.node_name:
                                if object_type == 'system':
                                    self.node_name = json_item['instance_name']
                                    logging.debug('found node name: %s', self.node_name)

                            if not self.units[key_id]:
                                self.units[key_id] = json_item['counter_unit']
                            break
        except KeyError:
            logging.warning('Found JSON object which doesn\'t hold expected contents. Object will '
                            'be ignored. It looks like: %s', json_item)

    def do_unit_conversions(self):
        """
        This method improves the presentation of some values through unit conversion. Don't call it
        before all data files are read!
        :return: None
        """
        for unit_key, unit in self.units.items():
            if unit == "B/s":
                self.tables[unit_key].expand_values(1 / (10 ** 6))
                self.units[unit_key] = "Mb/s"

            if unit == 'KB/s':
                self.tables[unit_key].expand_values(1 / (10 ** 3))
                self.units[unit_key] = "Mb/s"

            if unit == "microseconds":
                self.tables[unit_key].expand_values(1 / (10 ** 3))
                self.units[unit_key] = "milliseconds"
