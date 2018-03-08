"""
From here, the tool gets started. The module handles user communication, unpacks files if necessary
and decides, whether it has to run in perfstat or asup mode.
"""
import logging
import shutil
import os
import sys
import tempfile

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
    input_file, result_dir, sort_columns_by_name = picdat_util.handle_user_input(sys.argv)

    perfstat_output_files = None
    perfstat_console_file = None

    asup_info_file = None
    asup_data_files = None
    asup_header_file = None

    # handle directories as input
    if os.path.isdir(input_file):
        perfstat_output_files, perfstat_console_file = picdat_util.get_all_perfstats(input_file)

        if not perfstat_output_files:
            # check whether dir contains tgz files and extract them
            tar_files = [os.path.join(input_file, file) for file in os.listdir(
                os.path.abspath(input_file)) if picdat_util.data_type(file) == 'tgz']
            if tar_files:
                temp_path = tempfile.mkdtemp()
                counter = 0
                asup_data_files = []
                # collect all DATA files from tgz archive. As we only need one INFO and
                # HEADER file, it's ok to overwrite them each iteration
                for tar in tar_files:
                    asup_info_file, asup_data_file, asup_header_file = picdat_util.extract_tgz(
                        temp_path, tar, str(counter))
                    asup_data_files.append(asup_data_file)
                    counter = counter + 1
                
                    logging.debug('data file found: %s', asup_data_file)

            elif (os.path.isfile(os.path.join(input_file, constants.ASUP_INFO_FILE))
                  and os.path.isfile(os.path.join(input_file, constants.ASUP_DATA_FILE))):

                asup_info_file = os.path.join(input_file, constants.ASUP_INFO_FILE)
                asup_data_files = os.path.join(input_file, constants.ASUP_DATA_FILE)

                if os.path.isfile(os.path.join(input_file, constants.ASUP_HEADER_FILE)):
                    asup_header_file = os.path.join(input_file, constants.ASUP_HEADER_FILE)
                else:
                    logging.info('You gave a directory without a HEADER file. This means, some meta '
                                 'data for charts are missing such as node and cluster name.')

    # handle tar files as input
    elif picdat_util.data_type(input_file) == 'tgz':
        logging.info('Extract tgz...')
        temp_path = tempfile.mkdtemp()
        asup_info_file, asup_data_file, asup_header_file = picdat_util.extract_tgz(
            temp_path, input_file)
        asup_data_files = [asup_data_file]

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
    elif asup_data_files:
        # run in xml mode
        logging.info('Running picdat in xml mode')
        asup_mode.run_asup_mode(asup_info_file, asup_data_files, asup_header_file,
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
