"""
Contains the class XmlContainer. This class is responsible for holding and
processing all data collected from xml files.
"""
import logging
import datetime
from general.table import Table
from general import constants

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
# counter, but also in object (Contrary to 'SYSTEM_REQUESTS').
# The values found about one of the keys are meant to be visualized in one chart. So, each chart's
# table is about one counter and its columns will represent different instances.
OBJECT_REQUESTS = [('aggregate', 'total_transfers'), ('processor', 'processor_busy'),
                   ('volume', 'total_ops'), ('volume', 'avg_latency'), ('volume', 'read_data'),
                   ('volume', 'write_data'), ('lun:constituent', 'total_ops'),
                   ('lun:constituent', 'avg_latency'), ('lun:constituent', 'read_data'),
                   ('disk:constituent', 'disk_busy')]

# The following list contains search keys for gaining chart data. Its elements are the names of
# counters. The object tag belonging to the xml elements satisfying the keys is always
# 'system:constituent'. Therefore, object is not explicitly specified in the requests.
# The values found about all of these keys are meant to be visualized in one chart together. So,
# the columns of the chart's table will represent counters, means one column for each request.
SYSTEM_REQUESTS = ['hdd_data_read', 'hdd_data_written', 'net_data_recv', 'net_data_sent',
                   'ssd_data_read', 'ssd_data_written', 'fcp_data_recv', 'fcp_data_sent',
                   'tape_data_read', 'tape_data_written']
# constant holding 'system:constituant' as this is the object type belonging to the SYSTEM_REQUESTS
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

        # A dict of Table object, stored to a key from OBJECT_REQUESTS or SYSTEM_REQUESTS. Those
        # tables hold all collected chart data from xml data file for both request types.
        self.tables = {request: Table() for request in OBJECT_REQUESTS + [SYSTEM_OBJECT_TYPE]}

        # As it seems that the counters storing the values written in the data
        # file never get cleared, it is always necessary to calculate: (this_val
        # - last_val)/(this_timestamp - last_timestamp) to get a useful,
        # absolute value. For enabling this, the following dicts buffer the last
        # value and the last timestamp:
        self.value_buffer = {}
        self.unixtime_buffer = {}

        # A dict, mapping requests from both OBJECT_REQUESTS and SYSTEM_REQUESTS to the respective
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

            elif object_type == SYSTEM_OBJECT_TYPE and counter in SYSTEM_REQUESTS:
                self.units[SYSTEM_OBJECT_TYPE] = element_dict['unit']

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
                    unix_time = int(element_dict['timestamp'])
                    instance = element_dict['instance']
                    value = float(element_dict['value'])

                    if (object_type, counter, instance) in self.value_buffer:
                        # build absolute value through comparison of two consecutive values
                        last_val = self.value_buffer[(object_type, counter, instance)]
                        last_unixtime = self.unixtime_buffer[(object_type, counter, instance)]
                        abs_val = str((value - last_val) / (unix_time - last_unixtime))
                        date_time = datetime.datetime.fromtimestamp(unix_time)

                        logging.debug('object type %s: (recent_val - last_val)/(recent_time - '
                                      'last_time) = (%s - %s)/(%s - %s) = %s', object_type,
                                      value, last_val, unix_time, last_unixtime, abs_val)

                        self.tables[(object_type, counter)].insert(date_time, instance, abs_val)
                    self.value_buffer[(object_type, counter, instance)] = value
                    self.unixtime_buffer[(object_type, counter, instance)] = unix_time

                # process bases
                if (object_type, counter) in self.map_base_to_counter:
                    unix_time = int(element_dict['timestamp'])
                    instance = element_dict['instance']
                    baseval = float(element_dict['value'])
                    original_counter = self.map_base_to_counter[(object_type, counter)]

                    if (object_type, counter, instance) in self.baseval_buffer:
                        last_baseval = self.baseval_buffer[(object_type, counter, instance)]
                        last_unixtime = self.base_unixtime_buffer[(object_type, counter, instance)]
                        abs_baseval = str((baseval - last_baseval) / (unix_time - last_unixtime))
                        date_time = datetime.datetime.fromtimestamp(unix_time)

                        try:
                            old_value = self.tables[(object_type, original_counter)
                                                    ].get_item(date_time, instance)
                            try:
                                new_value = str(float(old_value) / float(abs_baseval))
                            except(ZeroDivisionError):
                                logging.debug(
                                    'base conversion leads to division by zero: %s/%s '
                                    '(%s:%s:%s) Set result to 0.', old_value, abs_baseval,
                                    object_type, instance, original_counter)
                                new_value = str(0)
                            self.tables[(object_type, original_counter)].insert(
                                date_time, instance, new_value)
                        except (KeyError, IndexError):
                            logging.debug(
                                'Found base before actual element. Add base element to base heap.')
                            logging.debug("base_element: %s", element_dict)
                            self.base_heap.add((object_type, original_counter,
                                                instance, date_time, abs_baseval))
                        except (ValueError):
                            logging.error('Found value which is not convertible to float. Base '
                                          'conversion failed.')

                    self.baseval_buffer[(object_type, counter, instance)] = baseval
                    self.base_unixtime_buffer[(object_type, counter, instance)] = unix_time

            # process SYSTEM_REQUESTS
            elif object_type == SYSTEM_OBJECT_TYPE:
                counter = element_dict['counter']
                if counter in SYSTEM_REQUESTS:
                    unix_time = int(element_dict['timestamp'])
                    value = float(element_dict['value'])

                    if (object_type, counter) in self.value_buffer:
                        # build absolute value through comparison of two consecutive values
                        last_val = self.value_buffer[(object_type, counter)]
                        last_unixtime = self.unixtime_buffer[(object_type, counter)]
                        abs_val = str((value - last_val) / (unix_time - last_unixtime))
                        date_time = datetime.datetime.fromtimestamp(unix_time)

                        self.tables[SYSTEM_OBJECT_TYPE].insert(date_time, counter, abs_val)
                    self.value_buffer[(object_type, counter)] = value
                    self.unixtime_buffer[(object_type, counter)] = unix_time

                    # once, save the node name
                    if not self.node_name:
                        self.node_name = element_dict['instance']

        except (KeyError):
            logging.warning(
                'Some tags inside an xml ROW element in DATA file seems to miss. Found following '
                'content: %s Expected (at least) following tags: object, counter, timestamp, '
                'instance, value', str(element_dict))

    def process_base_heap(self):
        """
        In case some base elements appear in xml before the elements, they are the base to, they
        will be thrown onto a heap to process them later. This method processes the heap content.
        It should be called after the data file is written.
        :return: None
        """
        for base_element in self.base_heap:
            object_type, counter, instance, timestamp, base_value = base_element
            try:
                old_value = self.tables[(object_type, counter)].get_item(timestamp, instance)
                new_value = str(float(old_value) / float(base_value))
                self.tables[(object_type, counter)].insert(timestamp, instance, new_value)
                logging.debug('base conversion. object: %s, counter: %s, instance: %s. value / '
                              'base = %s / %s = %s', object_type, counter, instance, old_value,
                              base_value, new_value)
            except (KeyError, IndexError):
                logging.warning(
                    'Found base value but no matching actual value. This means, Value for '
                    '%s - %s, instance %s with time stamp %s is missing in data!',
                    object_type, counter, instance, timestamp)
            except (ValueError):
                logging.error(
                    'Found value which is not convertible to float. Base conversion failed.')

    def do_unit_conversions(self):
        """
        This method improves the presentation of some values through unit conversion.
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

        if not self.tables[SYSTEM_OBJECT_TYPE].is_empty():
            flat_tables.append(self.tables[SYSTEM_OBJECT_TYPE].flatten('time', True))
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
        csv_names = [object_type.replace(':', '_') + '_' + aspect +
                     constants.CSV_FILE_ENDING for (object_type, aspect) in available_requests]

        # get identifiers for system:constituent chart
        if not self.tables[SYSTEM_OBJECT_TYPE].is_empty():
            titles.append(self.node_name)
            units.append(self.units[SYSTEM_OBJECT_TYPE])
            x_labels.append('time')
            object_ids.append(self.node_name.replace(':', '_').replace('-', '_'))
            barchart_booleans.append('false')
            csv_names.append(self.node_name.replace(':', '_').replace(
                '-', '_') + constants.CSV_FILE_ENDING)

        return {'titles': titles, 'units': units, 'x_labels': x_labels, 'object_ids': object_ids,
                'barchart_booleans': barchart_booleans, 'csv_names': csv_names}
