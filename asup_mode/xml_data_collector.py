"""
This module is for reading xml files, means both info and data file. It holds an XmlContainer
object which stores all collected data.
"""

import logging
import xml.etree.ElementTree as ET
from asup_mode.xml_container import XmlContainer

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

def read_header_file(header_file):
    """
    Gets meta data from HEADER file.
    :param header_file: Path to a HEADER file as string. May be None.
    :return: node name, cluster name, and time zone as strings. Values might be None.
    """
    node = None
    cluster = None
    timezone = None

    if header_file:

        with open(header_file, 'r') as file:
            for line in file:
                if 'X-Netapp-asup-hostname:' in line:
                    node = line.replace('X-Netapp-asup-hostname:', '').strip()
                if 'X-Netapp-asup-cluster-name:' in line:
                    cluster = line.replace('X-Netapp-asup-cluster-name:', '').strip()

                if 'X-Netapp-asup-generated-on:' in line:
                    timezone = line.replace('X-Netapp-asup-generated-on:', '').strip().split()[-2]

    return node, cluster, timezone


def read_info_file(container, asup_xml_info_file):
    """
    Reads a xml info file and collects unit and base information from it. Buffers xml 'ROW'
    elements and sends them one after another to the container for managing them.
    :param container: A XmlContainer object which holds all collected xml data
    :param asup_xml_info_file: The path to a 'CM-STATS-HOURLY-INFO.XML' file
    :return: None
    """
    elem_dict = {}

    for _, elem in ET.iterparse(asup_xml_info_file):
        tag = elem.tag.split('}', 1)[1]

        if tag == 'ROW':
            container.add_info(elem_dict)
            elem_dict = {}
        else:
            elem_dict[tag] = elem.text

        elem.clear()

    logging.debug('units: %s', str(container.units))
    logging.debug('bases: %s', str(container.base_dict))


def read_data_file(container, data_file):
    """
    Reads a xml data file and collects all useful information from it. Buffers
    xml 'ROW' elements and sends them one after another to the container for
    managing them. In the end, calls the XmlContainer.process_base_heap() method
    to perform remaining base conversions.
    :param container: A XmlContainer object which holds all collected xml data
    :param data_file: The path to a 'CM-STATS-HOURLY-DATA.XML' file
    :return: None
    """
    logging.debug('data file: %s', data_file)

    elem_dict = {}

    for _, elem in ET.iterparse(data_file):
        tag = elem.tag.split('}', 1)[1]

        if tag == 'ROW':
            container.add_data(elem_dict)
            elem_dict = {}
        else:
            elem_dict[tag] = elem.text

        elem.clear()

    logging.debug('remaining base elements: %s', str(container.base_heap))


def read_xmls(asup_xml_data_files, asup_xml_info_file, sort_columns_by_name):
    """
    This function analyzes both, the 'CM-STATS-HOURLY-DATA.XML' and the 'CM-STATS-HOURLY-INFO.XML'
    file. It holds a XmlContainer object to store collected information.
    :param asup_xml_data_files: list of paths to 'CM-STATS-HOURLY-DATA.XML' files (with unique name
    extensions)
    :param asup_xml_info_file: the path to a 'CM-STATS-HOURLY-INFO.XML' file
    :param sort_columns_by_name: A boolean, which determines whether the results should be sorted
    by name or by value instead. This will effect some of the returned tables (for some tables,
    sort by value doesn't make sense).
    :return: all chart data in tablelist format; ready to be written into csv tables. Additionally
    an label dict, which contains all required meta data about charts, labels or file names.
    """
    container = XmlContainer()

    logging.info('Read info file...')
    read_info_file(container, asup_xml_info_file)
    logging.info('Read data file(s)...')
    for data_file in asup_xml_data_files:
        logging.debug('read file %s', data_file)
        read_data_file(container, data_file)

    container.process_base_heap()
    container.do_unit_conversions()

    return container.get_flat_tables(sort_columns_by_name), container.build_label_dict()
