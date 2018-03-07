"""
This module is for reading xml files, means both info and data file. It holds an XmlContainer
object which stores all collected data.
"""

import logging
import xml.etree.ElementTree as ET
from xml_mode.xml_container import XmlContainer

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


def read_info_file(container, info_file):
    """
    Reads a xml info file and collects unit and base information from it. Buffers xml 'ROW'
    elements and sends them one after another to the container for managing them.
    :param container: A XmlContainer object which holds all collected xml data 
    :param info_file: The path to a 'CM-STATS-HOURLY-INFO.XML' file
    :return: None
    """
    elem_dict = {}

    for _, elem in ET.iterparse(info_file):
        tag = elem.tag.split('}', 1)[1]
        # print ('tag : %s, content: %s' % (elem.tag.split('}', 1)[1], elem.text))
        # elem.clear()

        if tag == 'ROW':
            container.add_info(elem_dict)
            elem_dict = {}
        else:
            elem_dict[tag] = elem.text

        elem.clear()


def read_data_file(container, data_file):
    """
    Reads a xml data file and collects all useful information from it. Buffers xml 'ROW' elements and
    sends them one after another to the container for managing them. In the end, calls the
    XmlContainer.process_base_heap() method to perform remaining base conversions.
    :param container: A XmlContainer object which holds all collected xml data 
    :param data_file: The path to a 'CM-STATS-HOURLY-DATA.XML' file
    :return: None
    """
    elem_dict = {}

    for _, elem in ET.iterparse(data_file):
        tag = elem.tag.split('}', 1)[1]

        if tag == 'ROW':
            container.add_item(elem_dict)
            elem_dict = {}
        else:
            elem_dict[tag] = elem.text

        elem.clear()

    logging.debug('remaining base elements: ' + str(container.base_heap))
    container.process_base_heap()


def read_xmls(data_file, info_file, sort_columns_by_name):
    """
    This function analyzes both, the 'CM-STATS-HOURLY-DATA.XML' and the 'CM-STATS-HOURLY-INFO.XML'
    file. It holds a XmlContainer object to store collected information.
    :param data_file: the path to a 'CM-STATS-HOURLY-DATA.XML' file
    :param info_file: the path to a 'CM-STATS-HOURLY-INFO.XML' file
    :return: all chart data in tablelist format; ready to be written into csv tables. Additionally
    an identifier dict, which contains all required meta data about charts, labels or file names.
    """
    container = XmlContainer()

    logging.info('Read info file...')
    read_info_file(container, info_file)
    logging.debug('units: ' + str(container.units))
    logging.info('Read data file...')
    read_data_file(container, data_file)

    return container.get_flat_tables(sort_columns_by_name), container.build_identifier_dict()
