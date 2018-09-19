"""
From here, the tool gets started. The module handles user communication, unpacks files if necessary
and decides, whether it has to run in perfstat or asup-xml or asup-hdf5 mode.
"""
import logging
import shutil
import os
import sys
import tempfile
import http.server

sys.path.append('..')

import picdat_util
from general import constants
from asup_mode import asup_mode
from perfstat_mode import perfstat_mode

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

try:
    temp_path = None

    # read command line options and take additional user input
    input_file, result_dir, sort_columns_by_name, webserver = picdat_util.handle_user_input(
        sys.argv)

    # initialize all accepted kinds of input files
    perfstat_output_files = None
    perfstat_console_file = None

    asup_xml_info_file = None
    asup_xml_data_files = None
    asup_xml_header_file = None

    asup_json_files = None

    asup_hdf5_file = None

    # handle directories as input
    if os.path.isdir(input_file):
        # try to select perfstat files from input dir
        perfstat_output_files, perfstat_console_file = picdat_util.get_all_perfstats(input_file)

        if not perfstat_output_files:
            # check whether dir contains tgz files and extract them
            tar_files = [os.path.join(input_file, file) for file in os.listdir(
                os.path.abspath(input_file)) if picdat_util.data_type(file) == 'tgz']
            if tar_files:
                temp_path = tempfile.mkdtemp()
                counter = 0
                asup_xml_data_files = []
                # collect all DATA files from tgz archive. As we only need one INFO and
                # HEADER file, it's ok to overwrite them each iteration
                for tar in sorted(tar_files):
                    logging.debug(tar)
                    asup_xml_info_file, asup_data_file, asup_xml_header_file = \
                    picdat_util.extract_tgz(temp_path, tar, str(counter))
                    asup_xml_data_files.append(asup_data_file)
                    counter = counter + 1

                    logging.debug('data file found: %s', asup_data_file)

            # try to select asup xml files from input dir if no perfstats and no tgz
            elif (os.path.isfile(os.path.join(input_file, constants.ASUP_INFO_FILE))
                  and os.path.isfile(os.path.join(input_file, constants.ASUP_DATA_FILE))):

                asup_xml_info_file = os.path.join(input_file, constants.ASUP_INFO_FILE)
                asup_xml_data_files = [os.path.join(input_file, constants.ASUP_DATA_FILE)]

                if os.path.isfile(os.path.join(input_file, constants.ASUP_HEADER_FILE)):
                    asup_xml_header_file = os.path.join(input_file, constants.ASUP_HEADER_FILE)
                else:
                    logging.info('You gave a directory without a HEADER file. This means, some '
                                 'meta data for charts are missing such as node and cluster name.')

            # check whether at least one file is of json data type
            elif any(picdat_util.data_type(file) == 'json'
                     for file in os.listdir(os.path.abspath(input_file))):
                logging.debug('Found json file(s) in dir')
                asup_json_files = [os.path.join(input_file, file)
                                   for file in os.listdir(os.path.abspath(input_file))
                                   if picdat_util.data_type(file) == 'json']
            else:
                picdat_util.ccma_check(os.listdir())

    # handle tar files as input
    elif picdat_util.data_type(input_file) == 'tgz':
        logging.info('Extract tgz...')
        temp_path = tempfile.mkdtemp()
        asup_xml_info_file, asup_data_file, asup_xml_header_file = picdat_util.extract_tgz(
            temp_path, input_file)
        asup_xml_data_files = [asup_data_file]

    # handle zip files or single .data or .out or .h5 files as input
    else:
        # extract zip if necessary
        if picdat_util.data_type(input_file) in ['data', 'out']:
            perfstat_output_files = [input_file]
        elif picdat_util.data_type(input_file) == 'zip':
            logging.info('Extract zip...')
            temp_path, perfstat_output_files, perfstat_console_file = picdat_util.extract_zip(
                input_file)
        elif picdat_util.data_type(input_file) == 'h5':
            asup_hdf5_file = input_file
        elif picdat_util.data_type(input_file) == 'json':
            asup_json_files = [input_file]

    # create directory and copy the necessary templates files into it
    csv_dir = picdat_util.prepare_directory(result_dir)

    # run
    if perfstat_output_files:
        # run in perfstat mode
        logging.info('Running PicDat in PerfStat mode')
        perfstat_mode.run_perfstat_mode(perfstat_console_file, perfstat_output_files, result_dir,
                                        csv_dir, sort_columns_by_name)
    elif asup_xml_data_files:
        # run in asup xml mode
        logging.info('Running PicDat in ASUP-xml mode')
        asup_mode.run_asup_mode_xml(asup_xml_info_file, asup_xml_data_files, asup_xml_header_file,
                                    result_dir, csv_dir, sort_columns_by_name)
    elif asup_hdf5_file:
        # run in asup hdf5 mode
        logging.info('Running PicDat in ASUP-hdf5 mode')
        asup_mode.run_asup_mode_hdf5(asup_hdf5_file, result_dir, csv_dir, sort_columns_by_name)
    elif asup_json_files:
        # run in asup json mode
        logging.info('Running PicDat in ASUP-json mode')
        asup_mode.run_asup_mode_json(asup_json_files, result_dir, csv_dir, sort_columns_by_name)
    else:
        logging.info('The input you gave (%s) doesn\'t contain any files this program can handle.',
                     input_file)
        sys.exit(0)

    # start web server if initiated with command line option
    if webserver:
        logging.info('Starting local web server... ')
        logging.info('Open \'localhost:8000\' in browser for viewing charts.')
        logging.info('Hit ctrl+C to terminate web server (might be necessary several times)')

        os.chdir(os.path.abspath(result_dir))
        server = http.server.HTTPServer(('', 8000), http.server.SimpleHTTPRequestHandler)
        server.serve_forever()
    else:
        logging.info('Done. You will find charts under: %s', os.path.abspath(result_dir))

finally:
    # delete temporarily extracted files
    if temp_path is not None:
        shutil.rmtree(temp_path)
        logging.info('(Temporarily extracted files deleted)')
