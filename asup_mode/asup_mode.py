"""
This module contains the main routines for the asup mode. Because the asup mode comprises
processing both xml and hdf5 files, there are two different main routines.
"""
import logging
import os
from asup_mode import xml_data_collector
from general import constants
from general import table_writer
from general import visualizer
from asup_mode import hdf5_data_collector

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


def run_asup_mode_xml(asup_xml_info_file, asup_xml_data_files, asup_xml_header_file, result_dir, csv_dir,
                  sort_columns_by_name):
    """
    The asup mode's main routine for processing xml files. Calls all functions to read xml data, 
    writes CSVs and finally creates an HTML.
    :param asup_xml_info_file: path to a 'CM-STATS-HOURLY-INFO.XML' file which contains unit and
    base information for the data file.
    :param asup_xml_data_files: list of paths to 'CM-STATS-HOURLY-DATA.XML' files.
    :param asup_xml_header_file: path to a 'HEADER' file. (Actually not an xml file; name is for
    distinction between asup xml and asup hdf5 mode)
    :param result_dir: path to an existing directory. Function stores its results in here.
    :param csv_dir: path to an existing directory inside result_dir. Function stores its csv tables
    in here.
    :param sort_columns_by_name: boolean, which says whether user wants to sort chart legends by
    name or by value. 
    :return: None
    """

    # collect data from file
    tables, label_dict = xml_data_collector.read_xmls(
        asup_xml_data_files, asup_xml_info_file, sort_columns_by_name)
    logging.debug('all labels: %s', label_dict)

    csv_filenames = [first_str.replace(':', '_').replace('-', '_') + '_' + 
                     second_str + constants.CSV_FILE_ENDING for first_str, second_str
                     in label_dict['identifiers']]
    csv_abs_filepaths = [csv_dir + os.sep + filename for filename in csv_filenames]
    csv_filelinks = [csv_dir.split(os.sep)[-1] + '/' + filename for filename in
                     csv_filenames]

    # write data into csv tables
    logging.info('Create csv tables...')
    table_writer.create_csv(csv_abs_filepaths, tables)

    # extract meta data from HEADER file:
    logging.info('Read header file...')
    node, cluster, timezone = xml_data_collector.read_header_file(asup_xml_header_file)
    logging.debug('cluster: %s, node: %s', cluster, node)
    if timezone:
        label_dict['timezone'] = timezone
    if cluster and node:
        html_title = 'Cluster: ' + cluster + '&ensp; &ensp; Node: ' + node
    else:
        html_title = os.path.abspath(os.path.dirname(asup_xml_info_file))

    # write html file
    html_filepath = os.path.join(result_dir, constants.HTML_FILENAME + constants.HTML_ENDING)
    logging.info('Create html file...')
    visualizer.create_html(html_filepath, csv_filelinks, html_title, label_dict)


def run_asup_mode_json(asup_json_files, result_dir, csv_dir, sort_columns_by_name):
    pass


def run_asup_mode_hdf5(asup_hdf5_file, result_dir, csv_dir, sort_columns_by_name):
    """
    The asup mode's main routine for processing hdf5 files. Calls all functions to read hdf5 data, 
    writes CSVs and finally creates an HTML.
    :param asup_hdf5_file: path to an .h5 file which contains performance data.
    :param result_dir: path to an existing directory. Function stores its results in here.
    :param csv_dir: path to an existing directory inside result_dir. Function stores its csv tables
    in here.
    :param sort_columns_by_name: boolean, which says whether user wants to sort chart legends by
    name or by value. 
    :return: None
    """
    tables, label_dict = hdf5_data_collector.read_hdf5(asup_hdf5_file, sort_columns_by_name)
    logging.debug('all labels: %s', label_dict)

    csv_filenames = [first_str.replace(':', '_').replace('-', '_') + '_' + 
                     second_str + constants.CSV_FILE_ENDING for first_str, second_str
                     in label_dict['identifiers']]
    csv_abs_filepaths = [csv_dir + os.sep + filename for filename in csv_filenames]
    csv_filelinks = [csv_dir.split(os.sep)[-1] + '/' + filename for filename in
                     csv_filenames]

    # write data into csv tables
    logging.info('Create csv tables...')
    table_writer.create_csv(csv_abs_filepaths, tables)

    # extract meta data from HEADER file:
    logging.info('Read header file...')
    html_title = os.path.abspath(os.path.dirname(asup_hdf5_file))

    # write html file
    html_filepath = os.path.join(result_dir, constants.HTML_FILENAME + constants.HTML_ENDING)
    logging.info('Create html file...')
    visualizer.create_html(html_filepath, csv_filelinks, html_title, label_dict)
