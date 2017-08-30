"""
From here, the tool gets started.
"""
import os
from shutil import copyfile
from collections import OrderedDict

import constants
import util
import data_collector
import table_writer
import visualizer

__author__ = 'Marie Lohbeck'
__copyright__ = 'Copyright 2017, Advanced UniByte GmbH'


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


def init(search_requests):
    """
    Sets the value for search_request.
    :param search_requests: Empty OrderedDict.
    :return: None
    """
    search_requests['aggregate'] = [('total_transfers', '/s')]
    search_requests['processor'] = [('processor_busy', '%')]
    search_requests['volume'] = [('total_ops', '/s'), ('avg_latency', 'us'), ('read_data', 'b/s')]
    search_requests['lun'] = [('total_ops', '/s'), ('avg_latency', 'ms'), ('read_data', 'b/s')]


def run(search_requests):
    """
    The tool's main routine. Calls all functions to read the data, write CSVs
    and finally create an HTML. Handles user communication.
    :param search_requests: An OrderedDict of lists which contains all requested object types
    mapped to the relating aspects and units which the tool should create graphs for.
    Might be empty, in this case the default height will be used.
    :return: None
    """

    print('Welcome to PicDat!')

    # receive PerfStat file from user:
    perfstat_output_file = input('Please enter a path to a PerfStat output file: ')
    if perfstat_output_file == '':
        perfstat_output_file = constants.DEFAULT_PERFSTAT_OUTPUT_FILE
    elif not os.path.isfile(perfstat_output_file):
        raise FileNotFoundError

    # receive destination directory from user
    destination_directory = input('Please select a destination directory for the results: ')
    if destination_directory != '':
        if os.path.isdir(destination_directory):
            destination_directory += os.sep
        else:
            raise NotADirectoryError

    destination_directory += constants.DEFAULT_DIRECTORY_NAME

    # get absolute path for PerfStat data file (just for using it as caption in resulting html)
    perfstat_output_absolute_path = os.path.abspath(perfstat_output_file)

    # collect data from file
    print('Read data...')
    collected_data = data_collector.read_data_file(perfstat_output_file, search_requests)
    tables_headers = collected_data['tables_headers']
    tables_content = collected_data['tables_content']
    timestamps = collected_data['timestamps']

    # create directory and copy the necessary dygraphs files into it
    print('Prepare directory...')
    final_dest_directory = util.empty_directory(destination_directory)
    dygraphs_js_dest = final_dest_directory + os.sep + 'dygraph.js'
    dygraphs_css_dest = final_dest_directory + os.sep + 'dygraph.css'
    copyfile(constants.DYGRAPHS_JS_SRC, dygraphs_js_dest)
    copyfile(constants.DYGRAPHS_CSS_SRC, dygraphs_css_dest)

    # generate file names for csv tables
    csv_filenames = util.get_csv_file_names(search_requests)
    csv_filepaths = [final_dest_directory + os.sep + filename for filename in csv_filenames]

    # write data into csv tables
    print('Create csv tables...')
    table_writer.create_csv(csv_filepaths, tables_headers, tables_content, timestamps)

    # frame html file path
    html_filepath = final_dest_directory + os.sep + constants.HTML_FILENAME

    # write html file
    print('Create html file...')
    visualizer.create_html(html_filepath, csv_filenames, search_requests, tables_headers,
                           perfstat_output_absolute_path)

    # finally
    print('Done. You will find graphs under: ' + html_filepath)


# run
init_search_requests = OrderedDict()
init(init_search_requests)
run(init_search_requests)
