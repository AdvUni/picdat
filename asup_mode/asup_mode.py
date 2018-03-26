"""
This module contains the main routine for the asup mode
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


def run_asup_mode_xml(asup_info_file, asup_data_files, asup_header_file, result_dir, csv_dir,
                  sort_columns_by_name):
    """
    The xml mode's main routine. Calls all functions to read xml data, write CSVs
    and finally creates an HTML.
    :param asup_info_file: path to a 'CM-STATS-HOURLY-INFO.XML' file which contains unit and base
    information for the data file.
    :param asup_data_files: list of paths to 'CM-STATS-HOURLY-DATA.XML' files.
    :param asup_header_file: path to a 'HEADER' file.
    :param result_dir: path to an existing directory. Function stores its results in here.
    :param csv_dir: path to an existing directory inside result_dir. Function stores its csv tables
    in here.
    :param sort_columns_by_name: boolean, which says whether user wants to sort chart legends by
    name or by value. 
    :return: None
    """

    # collect data from file
    tables, label_dict = xml_data_collector.read_xmls(
        asup_data_files, asup_info_file, sort_columns_by_name)
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
    node, cluster, timezone = xml_data_collector.read_header_file(asup_header_file)
    logging.debug('cluster: %s, node: %s', cluster, node)
    if timezone:
        label_dict['timezone'] = timezone
    if cluster and node:
        html_title = 'Cluster: ' + cluster + '&ensp; &ensp; Node: ' + node
    else:
        html_title = os.path.abspath(os.path.dirname(asup_info_file))

    # write html file
    html_filepath = os.path.join(result_dir, constants.HTML_FILENAME + constants.HTML_ENDING)
    logging.info('Create html file...')
    visualizer.create_html(html_filepath, csv_filelinks, html_title, label_dict)


def run_asup_mode_hdf5(hdf5_file, result_dir, csv_dir, sort_columns_by_name):
    tables, label_dict = hdf5_data_collector.read_hdf5(hdf5_file, sort_columns_by_name)
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
    html_title = os.path.abspath(os.path.dirname(hdf5_file))

    # write html file
    html_filepath = os.path.join(result_dir, constants.HTML_FILENAME + constants.HTML_ENDING)
    logging.info('Create html file...')
    visualizer.create_html(html_filepath, csv_filelinks, html_title, label_dict)
