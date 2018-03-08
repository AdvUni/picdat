"""
This module contains the main routine for the xml mode
"""
import logging
import os
from xml_mode import data_collector
from general import table_writer, constants
from general import visualizer

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

                # TODO: extract timezone

    return node, cluster, timezone


def run_xml_mode(xml_info_file, xml_data_file, xml_header_file, result_dir, csv_dir, sort_columns_by_name):
    """
    The xml mode's main routine. Calls all functions to read xml data, write CSVs
    and finally creates an HTML.
    :param xml_info_file: path to a 'CM-STATS-HOURLY-INFO.XML' file which contains unit and base
    information for the data file.
    :param xml_data_file: path to a 'CM-STATS-HOURLY-DATA.XML' file.
    :param xml_header_file: path to a 'HEADER' file.
    :param result_dir: path to an existing directory. Function stores its results in here.
    :param csv_dir: path to an existing directory inside result_dir. Function stores its csv tables
    in here.
    :param sort_columns_by_name: boolean, which says whether user wants to sort chart legends by
    name or by value. 
    :return: None
    """

    # collect data from file
    tables, identifier_dict = data_collector.read_xmls(
        xml_data_file, xml_info_file, sort_columns_by_name)
    logging.debug('all identifiers: %s', identifier_dict)

    csv_filenames = identifier_dict.pop('csv_names')
    csv_abs_filepaths = [csv_dir + os.sep + filename for filename in csv_filenames]
    csv_filelinks = [csv_dir.split(os.sep)[-1] + '/' + filename for filename in
                     csv_filenames]

    # write data into csv tables
    logging.info('Create csv tables...')
    table_writer.create_csv(csv_abs_filepaths, tables)

    # extract meta data from HEADER file:
    logging.info('Read header file...')
    node, cluster, timezone = read_header_file(xml_header_file)
    logging.debug('cluster: %s, node: %s', cluster, node)
    if timezone:
        identifier_dict['timezone'] = timezone
    if cluster and node:
        html_title = 'Cluster: ' + cluster + '&ensp; &ensp; Node: ' + node
    else:
        html_title = os.path.abspath(os.path.dirname(xml_info_file))

    # write html file
    html_filepath = os.path.join(result_dir, constants.HTML_FILENAME + constants.HTML_ENDING)
    logging.info('Create html file...')
    visualizer.create_html(html_filepath, csv_filelinks, html_title, identifier_dict)
