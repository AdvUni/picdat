'''

'''
import logging
import os
from xml_mode import data_collector
from general import table_writer
from general import visualizer

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


def run_xml_mode(info_file, data_file, result_dir, csv_dir, sort_columns_by_name):

    html_title = 'PicDat for XML'
    html_filepath = os.path.join(result_dir, 'charts.html')

    # collect data from file
    tables, identifier_dict = data_collector.read_xmls(data_file, info_file, sort_columns_by_name)
    logging.debug('tables: %s', tables)
    logging.debug('all identifiers: %s', identifier_dict)

    csv_filenames = identifier_dict.pop('csv_names')
    csv_abs_filepaths = [csv_dir + os.sep + filename for filename in csv_filenames]
    csv_filelinks = [csv_dir.split(os.sep)[-1] + '/' + filename for filename in
                     csv_filenames]

    # write data into csv tables
    logging.info('Create csv tables...')
    table_writer.create_csv(csv_abs_filepaths, tables)

    # write html file
    logging.info('Create html file...')
    visualizer.create_html(html_filepath, csv_filelinks, html_title, identifier_dict)