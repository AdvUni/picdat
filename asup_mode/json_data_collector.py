"""
This module is for reading performance data from json files, as trafero can extract them from
ASUPs. It holds an JsonContainer object which stores all collected data.
"""

import logging

try:
    import ijson
except ImportError:
    ijson = None
    print('Warning: Module ijson is not installed. PicDat won\'t be able to parse '
          'json files. If you try to run PicDat in asup json mode, it will crash. With PerfStats '
          'or asup xml files, everything is fine.')

from asup_mode.json_container import JsonContainer
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

def read_json(asup_json_files, sort_columns_by_name):
    """
    Reads json files and collects all data from it. Opens all files from list
    asup_json_files one after another and parses them with the ijson library. Ijson translates
    the json objects into python dicts. From the first of those dicts, function extracts cluster
    and node name. Every dict will be passed to the JsonContainer where it will be processed. In
    the end, function calles the container's unit conversion method.
    :param asup_json_files: List of filenames from files containing ASUP data in JSON format.
    :param sort_columns_by_name: A boolean, which determines whether the results should be sorted
    by name or by value instead. This will effect some of the returned tables (for some tables,
    sort by value doesn't make sense).
    :return: all chart data in tablelist format; ready to be written into csv tables. Additionally
    a label dict, which contains all required meta data about charts, labels or file names. At
    third, it returns a tuple of two strings which are cluster name and node name.
    """

    timezone = util.get_local_timezone()

    container = JsonContainer(timezone)
    logging.info('Read data file(s)...')

    # initialise variables to write cluster and node names to
    cluster_and_node = None

    for file in asup_json_files:
        with open (file, 'r') as json_file:
            logging.info("Read file %s", file)
            iterjson = ijson.items(json_file, 'item')

            # get cluster and node name from the first element of each file
            try:
                first_item = next(iterjson)
                try:
                    if not cluster_and_node:
                        cluster_and_node = first_item['cluster_name'], first_item['node_name']
                    else:
                        if cluster_and_node != (
                            first_item['cluster_name'], first_item['node_name']):
                            logging.error(
                                'inhomogeneous data: Different files in your input belong to '
                                'different clusters/nodes. PicDat output will probably not make '
                                'much sense.')
                except KeyError:
                    logging.warning('Tried to read cluster and node name from first object of '
                                    'file: %s, but it seems malformed. So, can\'t check those '
                                    'information. JSON object is: %s', file, first_item)
                    if not cluster_and_node:
                        cluster_and_node = '???', '???'

                # read data (first item and all others)
                container.add_data(first_item)
                for item in iterjson:
                    container.add_data(item)
            except StopIteration:
                logging.error(
                    'File %s does not contain any valid json content. It will be ignored.', file)

    # print information if charts are empty:
    for table_name, table in container.tables.items():
        if table.is_empty():
            logging.info('Search key had no hit: Table about %s is empty. Are you sure that your '
                         'json includes all available data about this search key?', table_name)

    container.do_unit_conversions()

    return util.get_flat_tables(container, sort_columns_by_name), \
        util.build_label_dict(container), cluster_and_node
