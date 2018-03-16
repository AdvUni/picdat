"""
Contains the class XmlContainer. This class is responsible for holding and
processing all data collected from xml files.
"""
import logging
from general.table import Table
from general import constants
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

INSTANCES_OVER_TIME_KEYS = [('aggregate', 'total_transfers'), ('processor', 'processor_busy'),
                            ('volume', 'total_ops'), ('volume', 'avg_latency'),
                            ('volume', 'read_data'), ('volume', 'write_data'),
                            ('lun:constituent', 'total_ops'), ('lun:constituent', 'avg_latency'),
                            ('lun:constituent', 'read_data'), ('disk:constituent', 'disk_busy')]

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
# data belonging to the key at runtime as well as for naming the resulting charts.
# For the objects of those keys, it is assumed, that each xml data file knows only one instance per
# object. So, each chart belonging to the keys is not meant to have several data series for
# different instances, but data series for different counters instead. This is why each key
# contains a whole set of counters. The counters in one set must of course wear all the same unit!
# The x axis of the charts will be 'time'. These two characteristics makes the keys different from
# the keys in the other lists, so this is why the list is called like this.
COUNTERS_OVER_TIME_KEYS = [
    ('bw', 'system:constituent', {'hdd_data_read', 'hdd_data_written', 'net_data_recv',
                                  'net_data_sent', 'ssd_data_read', 'ssd_data_written',
                                  'fcp_data_recv', 'fcp_data_sent', 'tape_data_read',
                                  'tape_data_written'}),
    ('iops', 'system:constituent', {'nfs_ops', 'cifs_ops', 'fcp_ops', 'iscsi_ops', 'other_ops'}),
    ('disk', 'raid', {'partial_stripes', 'full_stripes'})
]


class XmlContainer:
    """
    This class is responsible for holding and processing all data collected from xml files. It
    takes elements from xml files and saves them into tables, if they match the search requests.
    Furthermore, it does base conversion for values which need it and provides meta data like table
    names and axis labeling information.
    """

    def __init__(self):
        """
        Constructor for XmlContainer.
        """

        # set to hash all different object types appearing in INSTANCES_OVER_TIME_KEYS. Shall
        # reduce number of comparisons because some object types occur several times in
        # INSTANCES_OVER_TIME_KEYS.
        self.object_types = {request[0] for request in INSTANCES_OVER_TIME_KEYS}

        # A dict of Table objects. Each key from the three key lists has exactly one Table
        # storing all the matching data found in xml data file.
        self.tables = {request: Table()
                       for request in INSTANCES_OVER_TIME_KEYS + INSTANCES_OVER_BUCKET_KEYS}
        for request_id, object_type, _ in COUNTERS_OVER_TIME_KEYS:
            self.tables[object_type, request_id] = Table()

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

        # Same thing as base_heap, but it stores the bases for INSTANCES_OVER_BUCKET_KEYS instead.
        self.histo_base_heap = set()

        # To get a nice title for the last system chart, the program reads the node name from one
        # of the xml elements with object = system:constituent
        # Note: not in use at the moment
        self.node_name = None

    def add_info(self, element_dict):
        """
        Method takes the content from one 'ROW' xml element in a dict. If the element match a
        search request, its unit and base tag contents will be saved.
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
                for request_id, request_object, request_counters in COUNTERS_OVER_TIME_KEYS:
                    if object_type == request_object and counter in request_counters:
                        self.units[object_type, request_id] = element_dict['unit']

        except (KeyError):
            logging.warning(
                'Some tags inside an xml ROW element in INFO file seems to miss. Found following '
                'content: %s Expected (at least) following tags: object, counter, unit, base.',
                str(element_dict))

    def add_item(self, element_dict):
        """
        Method takes the content from one 'ROW' xml element in a dict. If the element match a
        search request, its data will be written into table data structures. If the element is a
        base to another element, the method tries to do the base conversion for this element.
        :param element_dict: A dict, mapping all xml tags inside a xml 'ROW' element to their text
        content
        :return: None
        """

        try:
            object_type = element_dict['object']

            # process INSTANCES_OVER_TIME_KEYS
            if object_type in self.object_types:
                counter = element_dict['counter']

                # process values
                if (object_type, counter) in INSTANCES_OVER_TIME_KEYS:
                    unixtimestamp = int(element_dict['timestamp'])
                    instance = element_dict['instance']
                    value = float(element_dict['value'])

                    if (object_type, counter, instance) in self.buffer:

                        # build absolute value through comparison of two consecutive values
                        abs_val, datetimestamp = util.get_abs_val(
                            value, unixtimestamp, self.buffer, (object_type, counter, instance))
                        self.tables[(object_type, counter)].insert(datetimestamp, instance, abs_val)

                    self.buffer[(object_type, counter, instance)] = (unixtimestamp, value)

                # process lun histo
                if (object_type, counter) in INSTANCES_OVER_BUCKET_KEYS:
                    unixtimestamp = int(element_dict['timestamp'])
                    instance = element_dict['instance']
                    valuelist = (element_dict['value']).split(',')

                    if (object_type, counter, instance) in self.buffer:
                        if self.buffer[object_type, counter, instance]:
                            abs_val_list, _ = util.get_abs_val(
                                valuelist, unixtimestamp, self.buffer, (object_type, counter, instance))

                            buckets = self.histo_labels[object_type, counter]
                            for bucket in range(len(buckets)):
                                self.tables[object_type, counter].insert(
                                    bucket, instance, abs_val_list[bucket])
                                logging.debug(
                                    '%s, %s, %s', buckets[bucket], instance, abs_val_list[bucket])

                            self.buffer[object_type, counter, instance] = None
                    else:
                        self.buffer[(object_type, counter, instance)
                                    ] = (unixtimestamp, valuelist)

                # process bases
                if (object_type, counter) in self.base_dict:
                    unixtimestamp = int(element_dict['timestamp'])
                    instance = element_dict['instance']
                    baseval = float(element_dict['value'])
                    original_counter = self.base_dict[(object_type, counter)]

                    if (object_type, counter, instance) in self.base_buffer:

                        # build absolute value through comparison of two consecutive values
                        abs_baseval, datetimestamp = util.get_abs_val(
                            baseval, unixtimestamp, self.base_buffer,
                            (object_type, counter, instance))

                        try:
                            self.do_base_conversion(
                                (object_type, original_counter), instance, datetimestamp, abs_baseval)
                        except (KeyError, IndexError):
                            logging.debug(
                                'Found base before actual element. Add base element to base heap. '
                                'Base_element: %s', element_dict)
                            self.base_heap.add((object_type, original_counter,
                                                instance, datetimestamp, abs_baseval))

                    self.base_buffer[(object_type, counter, instance)] = (unixtimestamp, baseval)

                if (object_type, counter) in self.histo_base_dict:
                    unixtimestamp = int(element_dict['timestamp'])
                    instance = element_dict['instance']
                    baseval = float(element_dict['value'])
                    original_counter = self.histo_base_dict[(object_type, counter)]

                    if (object_type, counter, instance) in self.base_buffer:
                        if self.base_buffer[object_type, counter, instance]:

                            # build absolute value through comparison of two consecutive values
                            abs_baseval, _ = util.get_abs_val(
                                baseval, unixtimestamp, self.base_buffer,
                                (object_type, counter, instance))

                            for bucket in range(len(self.histo_labels[object_type, original_counter])):
                                try:
                                    self.do_base_conversion(
                                        (object_type, original_counter), instance, bucket, float(abs_baseval))
                                except (KeyError, IndexError):
                                    logging.debug(
                                        'Found base before actual element. Add base element to base heap. '
                                        'Base_element: %s', element_dict)
                                    self.histo_base_heap.add(
                                        (object_type, original_counter, instance, bucket, abs_baseval))
                            self.base_buffer[object_type, counter, instance] = None
                    else:
                        self.base_buffer[object_type, counter,
                                         instance] = (unixtimestamp, baseval)

            else:
                for request_id, request_object, request_counters in COUNTERS_OVER_TIME_KEYS:
                    if object_type == request_object:
                        counter = element_dict['counter']
                        if counter in request_counters:
                            unixtimestamp = int(element_dict['timestamp'])
                            value = float(element_dict['value'])

                            if (object_type, counter) in self.buffer:

                                # build absolute value through comparison of two consecutive values
                                abs_val, datetimestamp = util.get_abs_val(
                                    value, unixtimestamp, self.buffer,
                                    (object_type, counter))
                                self.tables[object_type, request_id].insert(
                                    datetimestamp, counter, abs_val)

                            self.buffer[(object_type, counter)] = (unixtimestamp, value)

        except (KeyError):
            logging.warning(
                'Some tags inside an xml ROW element in DATA file seems to miss. Found following '
                'content: %s Expected (at least) following tags: object, counter, timestamp, '
                'instance, value', str(element_dict))

    def do_base_conversion(self, request, instance, rowname, base_val):
        """
        Does base conversion for a value stored in self.tables.
        :param request: key of dictionary self.tables to allocate table for a specific request
        :param instance: The object's instance name to which the value belongs which also is the
        name of the value's table column.
        :param rowname: The table row, to which the value should be inserted. It is a datetime
        object for most values or a bucket number, as the value belongs to a histogram.
        :param base_val: The value's base value.
        :return: None
        :raises KeyError: Will occur if the value is not stored in self.tables, means if
        self.tables[request] does not contain a value for given row and column.
        """
        try:
            old_val = self.tables[request].get_item(rowname, instance)
            try:
                new_val = str(float(old_val) / float(base_val))
            except(ZeroDivisionError):
                logging.debug(
                    'base conversion leads to division by zero: %s/%s (%s,%s) Set result to 0.',
                    old_val, base_val, request, instance)
                new_val = str(0)
            self.tables[request].insert(rowname, instance, new_val)
            logging.debug('base conversion. request: %s, instance: %s. value / base = %s / %s = %s',
                          request, instance, old_val, base_val, new_val)
        except(ValueError):
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
            object_type, counter, instance, datetimestamp, base_val = base_element
            try:
                self.do_base_conversion((object_type, counter), instance, datetimestamp, base_val)
            except (KeyError):
                logging.warning(
                    'Found base value but no matching actual value. This means, Value for '
                    '%s - %s, instance %s with time stamp %s is missing in data!',
                    object_type, counter, instance, datetimestamp)

        for base_element in self.histo_base_heap:
            object_type, counter, instance, bucket, base_val = base_element
            try:
                self.do_base_conversion((object_type, counter), instance, bucket, base_val)
            except (KeyError):
                logging.warning(
                    'Found base value but no matching actual value. This means, Value for '
                    '%s - %s, instance %s with time stamp %s is missing in data!',
                    object_type, counter, instance, bucket)

    def do_unit_conversions(self):
        """
        This method improves the presentation of some values through unit conversion. Don't call it
        before all data files are read!
        :return: None
        """
        for request, unit in self.units.items():
            if unit == 'percent':
                self.tables[request].expand_values(100)
                self.units[request] = '%'

            if unit == "b_per_sec":
                self.tables[request].expand_values(1 / (10**6))
                self.units[request] = "Mb/s"

            if unit == 'kb_per_sec':
                self.tables[request].expand_values(1 / (10**3))
                self.units[request] = "Mb/s"

    def get_flat_tables(self, sort_columns_by_name):
        flat_tables = [self.tables[request].flatten('time', sort_columns_by_name)
                       for request in INSTANCES_OVER_TIME_KEYS if not self.tables[request].is_empty()]

        if not self.tables[('lun:constituent', 'read_align_histo')].is_empty():
            flat_tables.append(
                self.tables[('lun:constituent', 'read_align_histo')].flatten('bucket', True))

        flat_tables = flat_tables + [self.tables[object_type, request_id].flatten(
            'time', True) for (request_id, object_type, _) in COUNTERS_OVER_TIME_KEYS]
        return flat_tables

    def build_identifier_dict(self):
        """
        This method provides meta information about the data found in the xml. Those are chart
        titles, units, x_labels, some object_ids, booleans, whether the resulting charts should be
        visualized as bar charts and names for the csv tables.
        :return: all mentioned information, packed into a dict
        """

        titles = []
        units = []
        x_labels = []
        object_ids = []
        barchart_booleans = []
        csv_names = []

        # get identifiers for all charts belonging to INSTANCES_OVER_TIME_KEYS
        available = [key for key in INSTANCES_OVER_TIME_KEYS if not self.tables[key].is_empty()]

        titles = titles + [key_object + ': ' + key_aspect for (key_object, key_aspect) in available]
        units = units + [self.units[key] for key in available]
        x_labels = x_labels + ['time' for _ in available]
        object_ids = object_ids + [key_object.replace(':', '_').replace('-', '_') + '_' +
                                   key_aspect for (key_object, key_aspect) in available]
        barchart_booleans = barchart_booleans + ['false' for _ in available]
        csv_names = csv_names + [key_object.replace(':', '_').replace('-', '_') + '_' + key_aspect +
                                 constants.CSV_FILE_ENDING for (key_object, key_aspect) in available]

        # get identifiers for all charts belonging to INSTANCE_OVER_BUCKET_KEYS
        available = [key for key in INSTANCES_OVER_BUCKET_KEYS if not self.tables[key].is_empty()]

        titles = titles + [key_object + ': ' + key_aspect for (key_object, key_aspect) in available]
        units = units + [self.units[key] for key in available]
        x_labels = x_labels + ['bucket' for _ in available]
        object_ids = object_ids + [key_object.replace(':', '_').replace('-', '_') + '_' +
                                   key_aspect for (key_object, key_aspect) in available]
        barchart_booleans = barchart_booleans + ['true' for _ in available]
        csv_names = csv_names + [key_object.replace(':', '_').replace('-', '_') + '_' + key_aspect +
                                 constants.CSV_FILE_ENDING for (key_object, key_aspect) in available]

        # get identifiers for all charts belonging to COUNTERS_OVER_TIME_KEYS
        available = [(key_object, key_id) for (key_id, key_object, _) in COUNTERS_OVER_TIME_KEYS
                     if not self.tables[key_object, key_aspect].is_empty()]

        titles = titles + [key_object + ': ' + key_id for (key_object, key_id) in available]
        units = units + [self.units[key] for key in available]
        x_labels = x_labels + ['time' for _ in available]
        object_ids = object_ids + [key_object.replace(':', '_').replace('-', '_') + '_' +
                                   key_id for (key_object, key_id) in available]
        barchart_booleans = barchart_booleans + ['false' for _ in available]
        csv_names = csv_names + [key_object.replace(':', '_').replace('-', '_') + '_' +
                                 key_id + constants.CSV_FILE_ENDING for (key_object, key_id) in available]

        return {'titles': titles, 'units': units, 'x_labels': x_labels, 'object_ids': object_ids,
                'barchart_booleans': barchart_booleans, 'csv_names': csv_names}
