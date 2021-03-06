"""
This module contains the main routine for the perfstat mode
"""
import logging
import os
import traceback

from perfstat_mode import util
from perfstat_mode import data_collector
from general import create_output
from general import constants
from general import table_writer
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


def run_perfstat_mode(perfstat_console_file, perfstat_output_files, result_dir, csv_dir,
                      sort_columns_by_name, compact_file):
    """
    The perfstat mode's main routine. Calls all functions to read perfstat data, write CSVs
    and finally create an HTML.
    :param perfstat_console_file: path to a console.log file which contains - if available - meta
    data for perfstats
    :param perfstat_output_files: list of paths to perfstat files like output.data or data.out.
    :param result_dir: path to an existing directory. Function stores its results in here.
    :param csv_dir: path to an existing directory inside result_dir. Function stores its csv tables
    in here.
    :param sort_columns_by_name: boolean, which says whether user wants to sort chart legends by
    name or by value.
    :param compact: Boolean, which says whether command line option 'compact' is set or not. If so,
    dygraphs code and csv content will be included into the charts html.
    :return: None
    """
    logging.debug("Perfstat output files: %s", perfstat_output_files)
    node_dict = None

    # if given, read cluster and node information from console.log file:
    if perfstat_console_file is not None:
        logging.info('Read console.log file for getting cluster and node names...')
        try:
            node_dict = util.read_console_file(perfstat_console_file)
        except KeyboardInterrupt:
            raise
        except:
            logging.info('Can\'t read console.log file for some reason: %s',
                         traceback.format_exc())
            node_dict = None
    else:
        logging.info('Did not find a console.log file to extract perfstat\'s cluster and node '
                     'name.')

    logging.debug('node dict: %s', str(node_dict))

    for perfstat_node in perfstat_output_files:

        # get nice names (if possible) for each PerfStat and the whole html file
        perfstat_address = perfstat_node.split(os.sep)[-2]

        if node_dict is None:
            html_title = perfstat_node
            node_identifier = perfstat_address
        else:
            try:
                node_identifier = node_dict[perfstat_address][1]
                html_title = util.get_html_title(node_dict, perfstat_address)
                logging.debug('html title (from identifier dict): %s', str(html_title))
            except KeyError:
                logging.info(
                    'Did not find a node name for address \'%s\' in \'console.log\'. Will '
                    'use just \'%s\' instead.', perfstat_address, perfstat_address)
                html_title = perfstat_node
                node_identifier = perfstat_address

            logging.info('Handle PerfStat from node "%s":', node_identifier)
        node_identifier += '_'

        if len(perfstat_output_files) == 1:
            node_identifier = ''

        # collect data from file
        logging.info('Read data...')
        tables, label_dict = data_collector.read_data_file(perfstat_node,
                                                           sort_columns_by_name)

        logging.debug('tables: %s', tables)
        logging.debug('all labels: %s', label_dict)

        create_output.create_output(
            result_dir, csv_dir, html_title, node_identifier, tables, label_dict, compact_file)

        # reset global variable 'localtimezone'
        util.localtimezone = None
