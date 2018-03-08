"""
Contains the class XmlContainer. This class is responsible for holding and processing all data collected from xml files.
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

REQUESTS = [('aggregate', 'total_transfers'), ('processor', 'processor_busy'), ('volume', 'total_ops'), ('volume',
                                                                                                         'avg_latency'), ('volume', 'read_data'), ('volume', 'write_data'), ('lun:constituent', 'total_ops'), ('lun:constituent', 'avg_latency'), ('lun:constituentS', 'read_data')]


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

        # set to hash all different object types appearing in REQUESTS. Shall reduce number of
        # comparisons because some object types occur several times in REQUESTS.
        self.object_types = {request[0] for request in REQUESTS}

        # A dict of Table object, stored to a key from REQUESTS. Those tables hold all collected
        # chart data from xml data file
        self.tables = {request: Table() for request in REQUESTS}

        # A dict, mapping requests from REQUEST to the respective unit. Units are provided by the
        # xml info file.
        self.units = {}

        # The following two dicts are for storing the information from xml base tags. There are two
        # of them to have easy access in both directions. There content is identical, just keys and
        # values are interchanged.
        self.map_counter_to_base = {}
        self.map_base_to_counter = {}

        self.value_buffer = {}
        self.baseval_buffer = {}

        # In case some base elements appear in xml before the elements, they are the base to, they
        # will be thrown into this set to process them later.
        self.base_heap = set()

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
            if object_type in self.object_types:
                counter = element_dict['counter']
                if (object_type, counter) in REQUESTS:
                    self.units[object_type, counter] = element_dict['unit']
                    base = element_dict['base']
                    if base:
                        self.map_counter_to_base[object_type, counter] = base
                        self.map_base_to_counter[object_type, base] = counter
        except (KeyError):
            logging.warning(
                'Some tags inside an xml ROW element seems to miss. Found following content: %s Expected (at least) following tags: object, counter, unit, base.', str(element_dict))

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
            if object_type in self.object_types:
                counter = element_dict['counter']

                if (object_type, counter) in REQUESTS:

                    timestamp = datetime.datetime.fromtimestamp(int(element_dict['timestamp']))
                    instance = element_dict['instance']
                    value = element_dict['value']

                    if (object_type, counter, instance) in self.value_buffer:
                        last_val = self.value_buffer[(object_type, counter, instance)]
                        abs_val = str((float(value) - float(last_val)) / 3600)

                        self.tables[(object_type, counter)].insert(timestamp, instance, abs_val)
                    self.value_buffer[(object_type, counter, instance)] = value

                if (object_type, counter) in self.map_base_to_counter:
                    timestamp = datetime.datetime.fromtimestamp(int(element_dict['timestamp']))
                    instance = element_dict['instance']
                    baseval = element_dict['value']
                    original_counter = self.map_base_to_counter[(object_type, counter)]

                    if (object_type, counter, instance) in self.baseval_buffer:
                        last_baseval = self.baseval_buffer[(object_type, counter, instance)]
                        abs_baseval = str((float(baseval) - float(last_baseval)) / 3600)

                        try:
                            old_value = self.tables[(object_type, original_counter)
                                                    ].get_item(timestamp, instance)
                            try:
                                new_value = str(float(old_value) / float(abs_baseval))
                            except(ZeroDivisionError):
                                logging.debug('base conversion leads to division by zero: %s/%s (%s:%s:%s) Set result to 0.',
                                              old_value, abs_baseval, object_type, instance, original_counter)
                                new_value = str(0)
                            self.tables[(object_type, original_counter)].insert(
                                timestamp, instance, new_value)
                        except (KeyError, IndexError):
                            logging.debug(
                                'Found base before actual element. Add base element to base heap.')
                            logging.debug("base_element: %s", element_dict)
                            self.base_heap.add((object_type, original_counter,
                                                instance, timestamp, abs_baseval))
                        except (ValueError):
                            logging.error(
                                'Found value which is not convertible to float. Base conversion failed.')

                    self.baseval_buffer[(object_type, counter, instance)] = baseval

        except (KeyError):
            logging.warning(
                'Some tags inside an xml ROW element seems to miss. Found following content: %s Expected (at least) following tags: object, counter, timestamp, instance, value', str(element_dict))

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
            except (KeyError, IndexError):
                logging.warning('Found base value but no matching actual value. This means, Value for %s - %s, instance %s with time stamp %s is missing in data!',
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

    def get_flat_tables(self, sort_columns_by_name):
        return [(self.tables[request]).flatten('time', sort_columns_by_name) for request in REQUESTS if not self.tables[request].is_empty()]

    def build_identifier_dict(self):
        """
        This method provides meta information about the data found in the xml. Those are chart
        titles, units, x_labels, some object_ids, booleans, whether the resulting charts should be
        visualized as bar charts and names for the csv tables.
        :return: all mentioned information, packed into a dict
        """
        available_requests = [
            request for request in REQUESTS if not self.tables[request].is_empty()]

        titles = [object_type + ': ' + aspect for (object_type, aspect) in available_requests]
        units = [self.units[request] for request in available_requests]
        x_labels = ['time' for _ in available_requests]
        object_ids = [object_type + '_' + aspect for (object_type, aspect) in available_requests]
        barchart_booleans = ['false' for _ in available_requests]
        csv_names = [object_type + '_' + aspect +
                     constants.CSV_FILE_ENDING for (object_type, aspect) in available_requests]

        return {'titles': titles, 'units': units, 'x_labels': x_labels, 'object_ids': object_ids,
                'barchart_booleans': barchart_booleans, 'csv_names': csv_names}
