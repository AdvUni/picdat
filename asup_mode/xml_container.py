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

# The following list contains search keys for gaining chart data. Its elements are tuples of
# objects and counters. The name 'object' is because different requests can not only differ in
# counter, but also in object (Contrary to 'SYSTEM_BW_REQUESTS').
# The values found about one of the keys are meant to be visualized in one chart. So, each chart's
# table is about one counter and its columns will represent different instances.
OBJECT_REQUESTS = [('aggregate', 'total_transfers'), ('processor', 'processor_busy'),
                   ('volume', 'total_ops'), ('volume', 'avg_latency'), ('volume', 'read_data'),
                   ('volume', 'write_data'), ('lun:constituent', 'total_ops'),
                   ('lun:constituent', 'avg_latency'), ('lun:constituent', 'read_data'),
                   ('disk:constituent', 'disk_busy')]

LUN_HISTO_REQUEST = ('lun:constituent', 'read_align_histo')

# The following list contains search keys for gaining chart data. Its elements are the names of
# counters. The counters are all about band with and are assumed to have the same unit. This is why
# the lists name contains 'BW'. The object tag belonging to the xml elements satisfying the keys is
# always 'system:constituent'. Therefore, object is not explicitly specified in the requests.
# The values found about all of these keys are meant to be visualized in one chart together. So,
# the columns of the chart's table will represent counters, means one column for each request.
SYSTEM_BW_REQUESTS = ['hdd_data_read', 'hdd_data_written', 'net_data_recv', 'net_data_sent',
                      'ssd_data_read', 'ssd_data_written', 'fcp_data_recv', 'fcp_data_sent',
                      'tape_data_read', 'tape_data_written']
# constant holding 'bw' to be part of a dict key for distinction between SYSTEM_BW_REQUESTS and
# SYSTEM_IOPS_REQUESTS results.
BW = 'bw'

# The following list contains search keys for gaining chart data. Its elements are the names of
# counters. The counters are all about iops operations and are assumed to have the same unit.
# This is why the lists name contains 'IOPS'. The object tag belonging to the xml
# elements satisfying the keys is always 'system:constituent'. Therefore, object is not explicitly
# specified in the requests. The values found about all of these keys are meant to be visualized in
# one chart together. So, the columns of the chart's table will represent counters, means one
# column for each request.
SYSTEM_IOPS_REQUESTS = ['nfs_ops', 'cifs_ops', 'fcp_ops', 'iscsi_ops', 'other_ops']
# constant holding 'iops' to be part of a dict key for distinction between SYSTEM_BW_REQUESTS and
# SYSTEM_IOPS_REQUESTS results.
IOPS = 'iops'

# constant holding 'system:constituant' as this is the object type
# belonging to the SYSTEM_BW_REQUESTS
SYSTEM_OBJECT_TYPE = 'system:constituent'


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

        # set to hash all different object types appearing in OBJECT_REQUESTS. Shall reduce number of
        # comparisons because some object types occur several times in OBJECT_REQUESTS.
        self.object_types = {request[0] for request in OBJECT_REQUESTS}

        # A dict of Table object, stored to a key from OBJECT_REQUESTS or SYSTEM_BW_REQUESTS. Those
        # tables hold all collected chart data from xml data file for both request types.
        self.tables = {request: Table() for request in OBJECT_REQUESTS + [LUN_HISTO_REQUEST,
                                                                          (SYSTEM_OBJECT_TYPE, BW), (SYSTEM_OBJECT_TYPE, IOPS)]}

        # As it seems that the counters storing the values written in the data
        # file never get cleared, it is always necessary to calculate: (this_val
        # - last_val)/(this_timestamp - last_timestamp) to get a useful,
        # absolute value. For enabling this, the following dicts buffer the last
        # value and the last timestamp:
        self.value_buffer = {}
        self.unixtime_buffer = {}

        # A dict, mapping requests from both OBJECT_REQUESTS and SYSTEM_BW_REQUESTS to the respective
        # unit. Units are provided by the xml info file.
        self.units = {}

        # The following two dicts are for storing the information from xml base tags. There are two
        # of them to have easy access in both directions. There content is identical, just keys and
        # values are interchanged.
        # Note: It is assumed, that values belonging to SYSTEM_REQUEST do not have any bases. So,
        # those dicts do only work for the OBJECT_REQUESTS
        self.map_counter_to_base = {}
        self.map_base_to_counter = {}
        # Does the same thing for bases as value_buffer and unixtime_buffer for values:
        self.baseval_buffer = {}
        self.base_unixtime_buffer = {}

        # In case some base elements appear in xml before the elements, they are the base to, they
        # will be thrown into this set to process them later.
        self.base_heap = set()

        # To get a nice title for the last system chart, the program reads the node name from one
        # of the xml elements with object = system:constituent
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
            if (object_type, counter) in OBJECT_REQUESTS:
                self.units[object_type, counter] = element_dict['unit']
                base = element_dict['base']
                if base:
                    self.map_counter_to_base[object_type, counter] = base
                    self.map_base_to_counter[object_type, base] = counter

            elif (object_type, counter) == LUN_HISTO_REQUEST:
                self.units[object_type, counter] = element_dict['unit']

            elif object_type == SYSTEM_OBJECT_TYPE:
                if counter in SYSTEM_BW_REQUESTS:
                    self.units[(SYSTEM_OBJECT_TYPE, BW)] = element_dict['unit']
                elif counter in SYSTEM_IOPS_REQUESTS:
                    self.units[(SYSTEM_OBJECT_TYPE, IOPS)] = element_dict['unit']

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

            # process OBJECT_REQUESTS
            if object_type in self.object_types:
                counter = element_dict['counter']

                # process values
                if (object_type, counter) in OBJECT_REQUESTS:
                    unixtimestamp = int(element_dict['timestamp'])
                    instance = element_dict['instance']
                    value = float(element_dict['value'])

                    if (object_type, counter, instance) in self.value_buffer:

                        # build absolute value through comparison of two consecutive values
                        abs_val, datetimestamp = util.get_abs_val(
                            value, unixtimestamp, self.value_buffer, self.unixtime_buffer,
                            (object_type, counter, instance))
                        self.tables[(object_type, counter)].insert(datetimestamp, instance, abs_val)

                    self.value_buffer[(object_type, counter, instance)] = value
                    self.unixtime_buffer[(object_type, counter, instance)] = unixtimestamp

                # process bases
                if (object_type, counter) in self.map_base_to_counter:
                    unixtimestamp = int(element_dict['timestamp'])
                    instance = element_dict['instance']
                    baseval = float(element_dict['value'])
                    original_counter = self.map_base_to_counter[(object_type, counter)]

                    if (object_type, counter, instance) in self.baseval_buffer:

                        # build absolute value through comparison of two consecutive values
                        abs_baseval, datetimestamp = util.get_abs_val(
                            baseval, unixtimestamp, self.baseval_buffer, self.base_unixtime_buffer,
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

                    self.baseval_buffer[(object_type, counter, instance)] = baseval
                    self.base_unixtime_buffer[(object_type, counter, instance)] = unixtimestamp

                # process lun histo
                if (object_type, counter) == LUN_HISTO_REQUEST:
                    unixtimestamp = int(element_dict['timestamp'])
                    instance = element_dict['instance']
                    valuelist = (element_dict['value']).split(',')
                    for bucket in range(len(valuelist)):
                        value = float(valuelist[bucket])

                        if (object_type, counter, instance, bucket) in self.value_buffer:

                            abs_val, _ = util.get_abs_val(value, unixtimestamp, self.value_buffer,
                                                          self.unixtime_buffer,
                                                          (object_type, counter, instance, bucket))
                            self.tables[LUN_HISTO_REQUEST].insert(bucket, instance, value)

                        self.value_buffer[(object_type, counter, instance, bucket)] = value
                        self.unixtime_buffer[(object_type, counter, instance,
                                              bucket)] = unixtimestamp

            # process SYSTEM_BW_REQUESTS and SYSTEM_IOPS_REQUESTS
            elif object_type == SYSTEM_OBJECT_TYPE:
                counter = element_dict['counter']
                if counter in SYSTEM_BW_REQUESTS:
                    unixtimestamp = int(element_dict['timestamp'])
                    value = float(element_dict['value'])

                    if (object_type, counter) in self.value_buffer:

                        # build absolute value through comparison of two consecutive values
                        abs_val, datetimestamp = util.get_abs_val(
                            value, unixtimestamp, self.value_buffer, self.unixtime_buffer,
                            (object_type, counter))
                        self.tables[(SYSTEM_OBJECT_TYPE, BW)].insert(
                            datetimestamp, counter, abs_val)

                    self.value_buffer[(object_type, counter)] = value
                    self.unixtime_buffer[(object_type, counter)] = unixtimestamp

                    # once, save the node name
                    if not self.node_name:
                        self.node_name = element_dict['instance']

                elif counter in SYSTEM_IOPS_REQUESTS:
                    unixtimestamp = int(element_dict['timestamp'])
                    value = float(element_dict['value'])

                    if (object_type, counter) in self.value_buffer:

                        # build absolute value through comparison of two consecutive values
                        abs_val, datetimestamp = util.get_abs_val(
                            value, unixtimestamp, self.value_buffer, self.unixtime_buffer,
                            (object_type, counter))
                        self.tables[(SYSTEM_OBJECT_TYPE, IOPS)].insert(
                            datetimestamp, counter, abs_val)

                    self.value_buffer[(object_type, counter)] = value
                    self.unixtime_buffer[(object_type, counter)] = unixtimestamp

                    # once, save the node name
                    if not self.node_name:
                        self.node_name = element_dict['instance']

        except (KeyError):
            logging.warning(
                'Some tags inside an xml ROW element in DATA file seems to miss. Found following '
                'content: %s Expected (at least) following tags: object, counter, timestamp, '
                'instance, value', str(element_dict))

    def do_base_conversion(self, request, instance, datetimestamp, base_val):
        """
        Does base conversion for a value stored in self.tables.
        :param request: key of dictionary self.tables to allocate table for a specific request
        :param instance: The object's instance name to which the value belongs which also is the
        name of the value's table column.
        :param datetimestamp: The time which belongs to the value in datetime format. It's also the
        name of the value's table row.
        :param base_val: The value's base value.
        :return: None
        :raises KeyError: Will occur if the value is not stored in self.tables, means if
        self.tables[request] does not contain a value for row datetimestamp and column instance.
        """
        try:
            old_val = self.tables[request].get_item(datetimestamp, instance)
            try:
                new_val = str(float(old_val) / float(base_val))
            except(ZeroDivisionError):
                logging.debug(
                    'base conversion leads to division by zero: %s/%s (%s,%s) Set result to 0.',
                    old_val, base_val, request, instance)
                new_val = str(0)
            self.tables[request].insert(datetimestamp, instance, new_val)
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
                       for request in OBJECT_REQUESTS if not self.tables[request].is_empty()]

        if not self.tables[LUN_HISTO_REQUEST].is_empty():
            flat_tables.append(self.tables[LUN_HISTO_REQUEST].flatten('bucket', True))

        if not self.tables[(SYSTEM_OBJECT_TYPE, BW)].is_empty():
            flat_tables.append(self.tables[(SYSTEM_OBJECT_TYPE, BW)].flatten('time', True))
        if not self.tables[(SYSTEM_OBJECT_TYPE, IOPS)].is_empty():
            flat_tables.append(self.tables[(SYSTEM_OBJECT_TYPE, IOPS)].flatten('time', True))
        return flat_tables

    def build_identifier_dict(self):
        """
        This method provides meta information about the data found in the xml. Those are chart
        titles, units, x_labels, some object_ids, booleans, whether the resulting charts should be
        visualized as bar charts and names for the csv tables.
        :return: all mentioned information, packed into a dict
        """

        # get identifiers for all charts belonging to OBJECT_REQUESTS
        available_requests = [
            request for request in OBJECT_REQUESTS if not self.tables[request].is_empty()]

        titles = [object_type + ': ' + aspect for (object_type, aspect) in available_requests]
        units = [self.units[request] for request in available_requests]
        x_labels = ['time' for _ in available_requests]
        object_ids = [object_type.replace(':', '_').replace('-', '_') + '_' +
                      aspect for (object_type, aspect) in available_requests]
        barchart_booleans = ['false' for _ in available_requests]
        csv_names = [object_type.replace(':', '_').replace('-', '_') + '_' + aspect +
                     constants.CSV_FILE_ENDING for (object_type, aspect) in available_requests]

        # get identifiers for chart belonging to LUN_HIST_REQUEST
        if not self.tables[LUN_HISTO_REQUEST].is_empty():
            titles.append(LUN_HISTO_REQUEST[0] + ': ' + LUN_HISTO_REQUEST[1])
            units.append(self.units[LUN_HISTO_REQUEST])
            x_labels.append('bucket')
            object_ids.append(LUN_HISTO_REQUEST[0].replace(
                ':', '_').replace('-', '_') + '_' + LUN_HISTO_REQUEST[1])
            barchart_booleans.append('true')
            csv_names.append(LUN_HISTO_REQUEST[0].replace(':', '_').replace(
                '-', '_') + '_' + LUN_HISTO_REQUEST[1] + constants.CSV_FILE_ENDING)

        # get identifiers for chart belonging to SYSTEM_BW_REQUESTS
        if not self.tables[(SYSTEM_OBJECT_TYPE, BW)].is_empty():
            titles.append(self.node_name + ': band width')
            units.append(self.units[(SYSTEM_OBJECT_TYPE, BW)])
            x_labels.append('time')
            object_ids.append(self.node_name.replace(':', '_').replace('-', '_') + '_' + BW)
            barchart_booleans.append('false')
            csv_names.append(self.node_name.replace(':', '_').replace(
                '-', '_') + '_' + BW + constants.CSV_FILE_ENDING)

        # get identifiers for chart belonging to SYSTEM_IOPS_REQUESTS
        if not self.tables[(SYSTEM_OBJECT_TYPE, IOPS)].is_empty():
            titles.append(self.node_name + ': IOPS')
            units.append(self.units[(SYSTEM_OBJECT_TYPE, IOPS)])
            x_labels.append('time')
            object_ids.append(self.node_name.replace(':', '_').replace('-', '_') + '_' + IOPS)
            barchart_booleans.append('false')
            csv_names.append(self.node_name.replace(':', '_').replace(
                '-', '_') + '_' + IOPS + constants.CSV_FILE_ENDING)

        return {'titles': titles, 'units': units, 'x_labels': x_labels, 'object_ids': object_ids,
                'barchart_booleans': barchart_booleans, 'csv_names': csv_names}
