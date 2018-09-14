"""
Contains the class XmlContainer. This class is responsible for holding and
processing all data collected from xml files.
"""
import logging
from general.table import Table
from asup_mode import util

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
# are written into the ASUP xml files. Several instances of the object will have data for the
# counter, so the resulting chart for each of the keys will have one data series per instance.
# The x axis of the charts will be 'time'. These two characteristics makes the keys different from
# the keys in the other lists, so this is why the list is called like this.

INSTANCES_OVER_TIME_KEYS = [('aggregate', 'total_transfers'),
                            ('ext_cache_obj', 'hya_reads_replaced'),
                            ('processor', 'processor_busy'), ('disk:constituent', 'disk_busy'),
                            ('volume', 'total_ops'), ('volume', 'avg_latency'),
                            ('volume', 'read_data'), ('volume', 'write_data'),
                            ('lun:constituent', 'total_ops'), ('lun:constituent', 'avg_latency'),
                            ('lun:constituent', 'read_data')]

# The following list contains search keys about histograms.
# Each element of the INSTANCES_OVER_BUCKET_KEYS list is a pair of an object and a counter, as they
# are written into the ASUP xml files. Several instances of the object will have data for the
# counter, so the resulting chart for each of the keys will have one data series per instance.
# As it is hardly useful, to draw a histogram as time diagram, the x axis will not be 'time', but
# 'bucket' here. These two characteristics makes the keys different from the keys in the other
# lists, so this is why the list is called like this.
INSTANCES_OVER_BUCKET_KEYS = [('lun:constituent', 'read_align_histo')]

# Each element of the COUNTERS_OVER_TIME_KEYS list is a triple of an identifier, an object and a
# set of counters. Objects and counters are some of those written into the ASUP xml files.
# The identifier is just for distinction between several keys of the list, because the objects are
# not unique and the counter sets are not very handy. The identifier is used for referencing the
# data belonging to the key at runtime as well as for naming the resulting charts and must be
# unique.
# For the objects of those keys, it is assumed, that each xml data file knows only one instance per
# object. So, each chart belonging to the keys is not meant to have several data series for
# different instances, but data series for different counters instead. This is why each key
# contains a whole set of counters. The counters in one set must of course wear all the same unit!
# The x axis of the charts will be 'time'. These two characteristics makes the keys different from
# the keys in the other lists, so this is why the list is called like this.
COUNTERS_OVER_TIME_KEYS = [
    ('bandwidth', 'system:constituent', {'hdd_data_read', 'hdd_data_written', 'net_data_recv',
                                         'net_data_sent', 'ssd_data_read', 'ssd_data_written',
                                         'fcp_data_recv', 'fcp_data_sent', 'tape_data_read',
                                         'tape_data_written'}),
    ('IOPS', 'system:constituent', {'nfs_ops', 'cifs_ops', 'fcp_ops', 'iscsi_ops', 'other_ops'}),
    ('fragmentation', 'raid', {'partial_stripes', 'full_stripes'})
]


class XmlContainer:
    """
    This class is responsible for holding and processing all data collected from xml files. It
    takes elements from xml files and saves them into tables, if they match the search keys.
    Furthermore, it does base conversion for values which need it and provides meta data like table
    names and axis labeling information.
    """

    def __init__(self):
        """
        Constructor for XmlContainer.
        """

        # A dict of Table objects. Each key from the three key lists has exactly one Table
        # storing all the matching data found in xml data file.
        self.tables = {searchkey: Table()
                       for searchkey in INSTANCES_OVER_TIME_KEYS + INSTANCES_OVER_BUCKET_KEYS}
        for key_id, _, _ in COUNTERS_OVER_TIME_KEYS:
            self.tables[key_id] = Table()

        # A dict for relating units to each search key from the three key lists.
        # Units are provided by the xml info file.
        self.units = {}

        # Histograms are charts with an x label different from 'time'. Which x values can occur is
        # precisely specified in the info file within the tag 'label1'.
        self.histo_labels = {}

        # As it seems that the counters storing the values written in the data
        # file never get cleared, it is always necessary to calculate: (this_val
        # - last_val)/(this_timestamp - last_timestamp) to get a useful,
        # absolute value. For enabling this, the following dict buffers the last timestamp and the
        # last value:
        self.buffer = {}

        # The following dict is for storing the information from xml base tags in the info file.
        # Its keys are tuples specifying object and the counter name of a base, its values are
        # the respective counters, to which the base belongs to.
        # Note: It is assumed, that values belonging to COUNTERS_OVER_TIME_KEYS do not have any
        # bases. So, those dicts do only work for the INSTANCES_OVER_TIME_KEYS
        self.base_dict = {}
        # Same thing as base_dict, but it stores the bases for INSTANCES_OVER_BUCKET_KEYS instead.
        self.histo_base_dict = {}

        # Does the same thing for bases as buffer for non-base values:
        self.base_buffer = {}

        # In case some base elements appear in xml before the elements, they are the base to, they
        # will be thrown into this set to process them later.
        self.base_heap = set()

        # To get a nice title for the last system chart, the program reads the node name from one
        # of the xml elements with object = system:constituent
        # Note: not in use at the moment
        self.node_name = None
        self.system_string = 'system:constituent'

    def add_info(self, element_dict):
        """
        Method takes the content from one 'ROW' xml element in a dict. If the element matches a
        search key, its unit and base tag contents will be saved.
        :param element_dict: A dict, mapping all xml tags inside a xml 'ROW' element to their text
        content
        :return: None
        """
        try:
            object_type = element_dict['object']
            counter = element_dict['counter']

            if (object_type, counter) in INSTANCES_OVER_TIME_KEYS:
                self.units[object_type, counter] = element_dict['unit']
                base = element_dict['base']
                if base:
                    self.base_dict[object_type, base] = counter

            elif (object_type, counter) in INSTANCES_OVER_BUCKET_KEYS:
                self.units[object_type, counter] = element_dict['unit']
                self.histo_labels[object_type, counter] = element_dict['label1'].split(',')
                base = element_dict['base']
                if base:
                    self.histo_base_dict[object_type, base] = counter

            else:
                for key_id, key_object, key_counters in COUNTERS_OVER_TIME_KEYS:
                    if object_type == key_object and counter in key_counters:
                        self.units[key_id] = element_dict['unit']

        except KeyError:
            logging.warning(
                'Some tags inside an xml ROW element in INFO file seems to miss. Found following '
                'content: %s Expected (at least) following tags: object, counter, unit, base.',
                str(element_dict))

    def add_data(self, element_dict):
        """
        Method takes the content from one 'ROW' xml element in a dict. If the element matches a
        search key, its data will be written into table data structures. If the element is a
        base to another element, the method tries to do the base conversion for this element.
        :param element_dict: A dict, mapping all xml tags inside a xml 'ROW' element to their text
        content
        :return: None
        """

        self.find_keys(element_dict)
        self.find_bases(element_dict)

    def find_keys(self, element_dict):
        """
        Method takes the content from one 'ROW' xml element in a dict and search it for all keys
        from INSTANCES_OVER_TIME_KEYS, INSTANCES_OVER_BUCKET_KEYS and COUNTERS_OVER_TIME_KEYS. If
        it finds something, it does the value conversion to get the absolute value and not only
        the recent total value of the counter, as it is written in the xml. Then it stores the
        value to the respective table and returns.
        :param element_dict: A dict, mapping all xml tags inside a xml 'ROW' element to their text
        content
        :return: None
        """
        try:
            object_type = element_dict['object']

            # collect node name once
            if not self.node_name:
                if object_type == 'system:constituent':
                    self.node_name = element_dict['instance']
                    logging.debug('found node name: %s', self.node_name)

            # process INSTANCES_OVER_TIME_KEYS
            for key_object, key_counter in INSTANCES_OVER_TIME_KEYS:
                if object_type == key_object:
                    counter = element_dict['counter']
                    if counter == key_counter:
                        logging.debug("%s %s", 'Found INSTANCES_OVER_BUCKET_KEY in: ', element_dict)
                        unixtimestamp = int(element_dict['timestamp'])
                        instance = element_dict['instance']
                        value = float(element_dict['value'])
                        try:
                            if (object_type, counter, instance) in self.buffer:

                                # build absolute value through comparison of two consecutive values
                                abs_val, datetimestamp = util.get_abs_val(
                                    value, unixtimestamp, self.buffer,
                                    (object_type, counter, instance))
                                self.tables[(object_type, counter)].insert(
                                    datetimestamp, instance, abs_val)

                            self.buffer[(object_type, counter, instance)] = (unixtimestamp, value)
                        except ZeroDivisionError:
                            # ZeroDivisionError occurs, if two consecutive timestamps are equal
                            logging.warning(
                                'Found an entry for an INSTANCES_OVER_TIME_KEY, which has '
                                'exactly the same time stamp as another entry belonging to '
                                'the same data series. Entry will be ignored. (timestamp: %s, '
                                'object: %s, counter: %s, instance: %s, value: %s) ',
                                unixtimestamp, object_type, counter, instance, value)
                        return

            # process INSTANCES_OVER_BUCKET_KEYS
            for key_object, key_counter in INSTANCES_OVER_BUCKET_KEYS:
                if object_type == key_object:
                    counter = element_dict['counter']
                    if counter == key_counter:
                        logging.debug("%s %s", 'Found INSTANCES_OVER_BUCKET_KEY in: ', element_dict)
                        unixtimestamp = int(element_dict['timestamp'])
                        instance = element_dict['instance']
                        valuelist = (element_dict['value']).split(',')

                        if (object_type, counter, instance) in self.buffer:
                            if self.buffer[object_type, counter, instance]:
                                try:
                                    # build absolute value through comparison of two consecutive
                                    # values
                                    abs_val_list, _ = util.get_abs_val(
                                        valuelist, unixtimestamp, self.buffer,
                                        (object_type, counter, instance))

                                    buckets = self.histo_labels[object_type, counter]
                                    for bucket in range(len(buckets)):
                                        self.tables[object_type, counter].insert(
                                            bucket, instance, abs_val_list[bucket])
                                        logging.debug('%s, %s, %s', buckets[bucket], instance,
                                                      abs_val_list[bucket])

                                    self.buffer[object_type, counter, instance] = None
                                except ZeroDivisionError :
                                    # ZeroDivisionError occurs, if two consecutive timestamps are
                                    # equal
                                    logging.warning(
                                        'Found an entry for an INSTANCES_OVER_BUCKET_KEY, which '
                                        'has exactly the same time stamp as another entry '
                                        'belonging to the same data series. Entry will be '
                                        'ignored. '
                                        '(timestamp: %s, counter: %s, instance: %s, values: %s) ',
                                        unixtimestamp, counter, instance, valuelist)
                        else:
                            self.buffer[(object_type, counter, instance)] = (
                                unixtimestamp, valuelist)
                        return

            # Process COUNTERS_OVER_TIME_KEYS
            for key_id, key_object, key_counters in COUNTERS_OVER_TIME_KEYS:
                if object_type == key_object:
                    counter = element_dict['counter']
                    if counter in key_counters:

                        logging.debug("%s %s", 'found COUNTERS_OVER_TIME_KEY in: ', element_dict)
                        unixtimestamp = int(element_dict['timestamp'])
                        value = float(element_dict['value'])
                        try:
                            if (object_type, counter) in self.buffer:

                                # build absolute value through comparison of two consecutive values
                                abs_val, datetimestamp = util.get_abs_val(
                                    value, unixtimestamp, self.buffer, (object_type, counter))
                                self.tables[key_id].insert(datetimestamp, counter, abs_val)

                            self.buffer[(object_type, counter)] = (unixtimestamp, value)
                        except ZeroDivisionError:
                            # ZeroDivisionError occurs, if two consecutive timestamps are equal
                            logging.warning(
                                'Found an entry for a COUNTERS_OVER_TIME_KEY, which has '
                                'exactly the same time stamp as another entry belonging to '
                                'the same data series. Entry will be ignored. (timestamp: %s, '
                                'counter: %s, instance: %s, value: %s) ',
                                unixtimestamp, counter, instance, value)
                        return
        except KeyError:
            logging.warning(
                'Some tags inside an xml ROW element in DATA file seems to miss. Found following '
                'content: %s Expected (at least) following tags: object, counter, timestamp, '
                'instance, value', str(element_dict))

    def find_bases(self, element_dict):
        """
        Method takes the content from one 'ROW' xml element in a dict and search it for base values
        from self.base_dict and self.histo_base_dict. If it finds something, it does the value
        conversion to get the absolute value and not only the recent total value of the counter, as
        it is written in the xml. Then it tries to do the base conversion. If this fails, because
        the base value was collected before the value the base belongs to, the method stores the
        base to self.base_heap. It will be processed later.
        :param element_dict: A dict, mapping all xml tags inside a xml 'ROW' element to their text
        content
        :return: None
        """
        try:
            object_type = element_dict['object']

            # process bases for INSTANCES_OVER_TIME_KEYS
            for base_object, base_counter in self.base_dict:
                if object_type == base_object:
                    counter = element_dict['counter']
                    if counter == base_counter:
                        unixtimestamp = int(element_dict['timestamp'])
                        instance = element_dict['instance']
                        baseval = float(element_dict['value'])

                        try:
                            if (object_type, counter, instance) in self.base_buffer:

                                # build absolute value through comparison of two consecutive values
                                abs_baseval, datetimestamp = util.get_abs_val(
                                    baseval, unixtimestamp, self.base_buffer,
                                    (object_type, counter, instance))

                                original_counter = self.base_dict[(object_type, counter)]
                                try:
                                    self.do_base_conversion((object_type, original_counter),
                                                            instance, datetimestamp, abs_baseval)
                                except (KeyError, IndexError):
                                    logging.debug(
                                        'Found base before actual element. Add base element to '
                                        'base heap. Base_element: %s', element_dict)
                                    self.base_heap.add((object_type, original_counter,
                                                        instance, datetimestamp, abs_baseval))

                            self.base_buffer[(object_type, counter, instance)
                                             ] = (unixtimestamp, baseval)
                        except ZeroDivisionError :
                            # ZeroDivisionError occurs, if two consecutive timestamps are equal
                            logging.warning(
                                'Found an entry for a base, which has '
                                'exactly the same time stamp as another entry belonging to '
                                'the same base. Entry will be ignored. (timestamp: %s, '
                                'object: %s, counter: %s, instance: %s, value: %s) ',
                                unixtimestamp, object_type, counter, instance, baseval)

            # process bases for INSTANCES_OVER_BUCKET_KEYS
            for base_object, base_counter in self.histo_base_dict:
                if object_type == base_object:
                    counter = element_dict['counter']
                    if counter == base_counter:
                        unixtimestamp = int(element_dict['timestamp'])
                        instance = element_dict['instance']
                        baseval = float(element_dict['value'])

                        if (object_type, counter, instance) in self.base_buffer:
                            if self.base_buffer[object_type, counter, instance]:
                                try:
                                    # build absolute value through comparison of two consecutive
                                    # values
                                    abs_baseval, _ = util.get_abs_val(
                                        baseval, unixtimestamp, self.base_buffer,
                                        (object_type, counter, instance))

                                    original_counter = self.histo_base_dict[(object_type, counter)]
                                    for bucket in range(len(
                                        self.histo_labels[object_type, original_counter])):
                                        try:
                                            self.do_base_conversion(
                                                (object_type, original_counter),
                                                instance, bucket, float(abs_baseval))
                                        except (KeyError, IndexError):
                                            logging.debug(
                                                'Found base before actual element. Add base '
                                                'element to base heap. Base_element: %s',
                                                element_dict)
                                            self.base_heap.add((object_type, original_counter,
                                                                instance, bucket, abs_baseval))
                                    self.base_buffer[object_type, counter, instance] = None
                                except ZeroDivisionError:
                                    # ZeroDivisionError occurs, if two consecutive timestamps are
                                    # equal
                                    logging.warning(
                                        'Found an entry for a base, which has exactly the same '
                                        'time stamp as another entry belonging to '
                                        'the same base. Entry will be ignored. (timestamp: '
                                        '%s, object: %s, counter: %s, instance: %s, value: %s) ',
                                        unixtimestamp, object_type, counter, instance, baseval)

                        else:
                            self.base_buffer[object_type, counter,
                                             instance] = (unixtimestamp, baseval)

        except KeyError:
            logging.warning(
                'Some tags inside an xml ROW element in DATA file seems to miss. Found following '
                'content: %s Expected (at least) following tags: object, counter, timestamp, '
                'instance, value', str(element_dict))

    def do_base_conversion(self, tablekey, instance, rowname, base_val):
        """
        Does base conversion for a value stored in self.tables.
        :param tablekey: key of dictionary self.tables to allocate table for a specific tablekey
        :param instance: The object's instance name to which the value belongs which also is the
        name of the value's table column.
        :param rowname: The table row, to which the value should be inserted. It is a datetime
        object for most values or a bucket number, as the value belongs to a histogram.
        :param base_val: The value's base value.
        :return: None
        :raises KeyError: Will occur if the value is not stored in self.tables, means if
        self.tables[tablekey] does not contain a value for given row and column.
        """
        try:
            old_val = self.tables[tablekey].get_item(rowname, instance)
            try:
                new_val = str(float(old_val) / float(base_val))
            except ZeroDivisionError:
                logging.debug(
                    'base conversion leads to division by zero: %s/%s (%s,%s) Set result to 0.',
                    old_val, base_val, tablekey, instance)
                new_val = str(0)
            self.tables[tablekey].insert(rowname, instance, new_val)
            logging.debug('base conversion. tablekey: %s, instance: %s. value / base = '
                          '%s / %s = %s', tablekey, instance, old_val, base_val, new_val)
        except ValueError:
            logging.error(
                'Found value which is not convertible to float. Base conversion failed.')
        except(KeyError, IndexError):
            raise KeyError

    def process_base_heap(self):
        """
        In case some base elements appear in xml before the elements, they are the base to, they
        will be thrown onto a heap to process them later. This method processes the heap content.
        Don't call it before all data files are read!
        :return: None
        """
        for base_element in self.base_heap:
            object_type, counter, instance, row, base_val = base_element
            try:
                self.do_base_conversion((object_type, counter), instance, row, base_val)
            except KeyError:
                logging.warning(
                    'Found base value but no matching actual value. This means, Value for '
                    '%s - %s, instance %s with time stamp/bucket %s is missing in data!',
                    object_type, counter, instance, row)

    def do_unit_conversions(self):
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
                self.tables[unit_key].expand_values(1 / (10 ** 6))
                self.units[unit_key] = "Mb/s"

            if unit == 'kb_per_sec':
                self.tables[unit_key].expand_values(1 / (10 ** 3))
                self.units[unit_key] = "Mb/s"

    def get_flat_tables(self, sort_columns_by_name):
        """
        Calls the flatten method for each table from self.tables, which is not empty.
        :param sort_columns_by_name: boolean, whether table columns should be sorted
        by names. If False, they will be sorted by value. Tables for
        COUNTERS_OVER_TIME_KEYS will always be sorted by names, because this is considered
        to be a clearer arrangement.
        :return: all not-empty flattened tables in a list.
        """
        flat_tables = []

        flat_tables = flat_tables + [self.tables[key].flatten('time', sort_columns_by_name)
                                     for key in INSTANCES_OVER_TIME_KEYS
                                     if not self.tables[key].is_empty()]

        flat_tables = flat_tables + [self.tables[key].flatten('bucket', sort_columns_by_name)
                                     for key in INSTANCES_OVER_BUCKET_KEYS
                                     if not self.tables[key].is_empty()]

        flat_tables = flat_tables + [self.tables[key_id].flatten('time', True)
                                     for (key_id, _, _) in COUNTERS_OVER_TIME_KEYS
                                     if not self.tables[key_id].is_empty()]
        return flat_tables