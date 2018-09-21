import logging
import os
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


def create_output(result_dir, csv_dir, html_title, output_label, tables, label_dict, compact):

    csv_abs_filepaths, csv_filelinks = csv_naming(label_dict['identifiers'], csv_dir, output_label)

    # write data into csv tables
    logging.info('Create csv tables...')
    table_writer.create_csv(csv_abs_filepaths, tables)

    # write html file
    html_filepath = os.path.join(
        result_dir, output_label + constants.HTML_FILENAME + constants.HTML_ENDING)
    logging.info('Create html file...')
    visualizer.create_html(html_filepath, csv_strings(csv_abs_filepaths, csv_filelinks, compact),
                           html_title, label_dict, compact)


def csv_strings(csv_abs_filepaths, csv_filelinks, compact):
    if compact:
        csv_content_list = []
        for path in csv_abs_filepaths:
            with open(path, 'r') as csv:
                csv_content_list += [csv.read()]
        return csv_content_list

    return csv_filelinks


def csv_naming(identifiers, csv_dir, output_label):
    csv_filenames = [output_label + first_str.replace(':', '_').replace('-', '_') + '_'
                     +second_str + constants.CSV_FILE_ENDING for first_str, second_str
                     in identifiers]
    csv_abs_filepaths = [csv_dir + os.sep + filename for filename in csv_filenames]
    csv_filelinks = [csv_dir.split(os.sep)[-1] + '/' + filename for filename in
                     csv_filenames]

    return csv_abs_filepaths, csv_filelinks
