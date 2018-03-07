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

    # create directory and copy the necessary templates files into it
    csv_dir = picdat_util.prepare_directory(result_dir)

    if picdat_util.data_type(input_file) == 'tgz':
        # run in xml mode
        logging.info('Running picdat in xml mode')
        temp_path, info_file, data_file = picdat_util.extract_tgz(input_file)
        xml_mode.run_xml_mode(info_file, data_file, result_dir, csv_dir, sort_columns_by_name)

    else:
        # run in perfstat mode
        logging.info('Running picdat in perfstat mode')
        perfstat_output_files = None
        console_file = None

        # extract zip if necessary
        if os.path.isdir(input_file):
            perfstat_output_files, console_file = picdat_util.get_all_perfstats(input_file)
        elif picdat_util.data_type(input_file) in ['data', 'out']:
            perfstat_output_files = [input_file]
        elif picdat_util.data_type(input_file) == 'zip':
            logging.info('Extract zip...')
            temp_path, perfstat_output_files, console_file = picdat_util.extract_zip(input_file)
        # interrupt program if there are no .data files found
        if not perfstat_output_files:
            logging.info('The input you gave (%s) doesn\'t contain any .data files.', input_file)
            sys.exit(0)

        perfstat_mode.run_perfstat_mode(
            console_file, perfstat_output_files, result_dir, csv_dir, sort_columns_by_name)

    logging.info('Done. You will find charts under: %s', os.path.abspath(result_dir))

finally:
    # delete temporarily extracted files
    if temp_path is not None:
        shutil.rmtree(temp_path)
        logging.info('(Temporarily extracted files deleted)')
