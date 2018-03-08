"""
From here, the tool gets started. The module handles user communication, unpacks files if necessary
and decides, whether it has to run in perfstat or xml mode.
"""
import logging
import shutil
import os
import sys

sys.path.append('..')

import picdat_util
from general import constants
from xml_mode import xml_mode
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
    input_file, result_dir, sort_columns_by_name = picdat_util.handle_user_input(sys.argv)

    perfstat_output_files = None
    perfstat_console_file = None

    xml_info_file = None
    xml_data_file = None
    xml_header_file = None

    # handle directories as input
    if os.path.isdir(input_file):
        perfstat_output_files, perfstat_console_file = picdat_util.get_all_perfstats(input_file)
        if (not perfstat_output_files
            and os.path.isfile(os.path.join(input_file, constants.XML_INFO_FILE))
                and os.path.isfile(os.path.join(input_file, constants.XML_DATA_FILE))):
            xml_info_file = os.path.join(input_file, constants.XML_INFO_FILE)
            xml_data_file = os.path.join(input_file, constants.XML_DATA_FILE)
            if os.path.isfile(os.path.join(input_file, constants.XML_HEADER_FILE)):
                xml_header_file = os.path.join(input_file, constants.XML_HEADER_FILE)
            else:
                logging.info('You gave a directory without a HEADER file. This means, some meta '
                             'data for charts are missing such as node and cluster name.')

    # handle tar files as input
    elif picdat_util.data_type(input_file) == 'tgz':
        logging.info('Extract tgz...')
        temp_path, xml_info_file, xml_data_file, xml_header_file = picdat_util.extract_tgz(
            input_file)

    # handle zip files or single .data or .out files as input
    else:
        # extract zip if necessary
        if picdat_util.data_type(input_file) in ['data', 'out']:
            perfstat_output_files = [input_file]
        elif picdat_util.data_type(input_file) == 'zip':
            logging.info('Extract zip...')
            temp_path, perfstat_output_files, perfstat_console_file = picdat_util.extract_zip(
                input_file)

    # create directory and copy the necessary templates files into it
    csv_dir = picdat_util.prepare_directory(result_dir)

    # decide whether run in perfstat or xml mode
    if perfstat_output_files:
        # run in perfstat mode
        logging.info('Running picdat in perfstat mode')
        perfstat_mode.run_perfstat_mode(perfstat_console_file, perfstat_output_files, result_dir,
                                        csv_dir, sort_columns_by_name)
    elif xml_data_file:
        # run in xml mode
        logging.info('Running picdat in xml mode')
        xml_mode.run_xml_mode(xml_info_file, xml_data_file, xml_header_file,
                              result_dir, csv_dir, sort_columns_by_name)
    else:
        logging.info('The input you gave (%s) doesn\'t contain any files this program can handle.',
                     input_file)
        sys.exit(0)

    logging.info('Done. You will find charts under: %s', os.path.abspath(result_dir))


finally:
    # delete temporarily extracted files
    if temp_path is not None:
        shutil.rmtree(temp_path)
        logging.info('(Temporarily extracted files deleted)')
