"""
PicDat has the perfstat mode, the asup xml mode and the asup json mode (and asup hdf5 mode). Each
mode is for a different kind of performance data, because each kind needs to be handled
differently. But after the input files are read, writing csv tables and visualising them with html
- in short: creating the output - works in the same way for each of the modes. Therefore, this
module summarises the functionality of creating the output, so that each mode can call it.
"""
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
    """
    Calls the table_collector and the visualizer module which create csv and html files.
    :param result_dir: path to an existing directory. Function stores its results in here.
    :param csv_dir: path to an existing directory inside result_dir. Function stores its csv tables
    in here.
    :param html_title: Some string describing the processed performance data, for example naming
    the cluster and the node. Will be written to the top of the html document.
    :param output_label: Also a string describing the performance data, but in a shorter way and
    without white spaces. Will be embedded into file names for a better overview and/or distinction
    between different html files.
    :param tables: Nested lists which contain all data, ready to be written into csv files.
    :param label_dict: A dict containing meta data such as axis labels or names for the charts
    the tables)
    :param compact: Boolean, which says whether command line option 'compact' is set or not. If so,
    dygraphs code and csv content will be included into the charts html.
    :return: None.
    """

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


def csv_naming(identifiers, csv_dir, output_label):
    """
    Does stuff with csv paths. Creates two lists: The first contains an absolute file path
    for each csv table file, the second contains a so-called file link for each csv table file.
    It is called link to be distinguished from the absolute or relative path. More specific,
    it actually is a path, but seen relatively from the html location. Furthermore, its seperator
    is always /, even under windows machines, because the links are used to reference inside the
    html.
    :param identifiers: List of tuples, one tuple for each chart/csv file, each tuple consists of
    two strings and is a unique identifier for its chart. Function will generate the csv filenames
    under usage of the identifiers.
    :param csv_dir: Directory, which will contain the csv tables. Function uses it to generate the
    absolute file paths.
    :param output_label: A string describing the whole performance data, for example with cluster
    and node name. Will be embedded into file names for a better overview and/or distinction
    between different nodes files.
    :return: csv_abs_filepaths and csv_filelinks as described.
    """
    csv_filenames = [output_label + first_str.replace(':', '_').replace('-', '_') + '_'
                     +second_str + constants.CSV_FILE_ENDING for first_str, second_str
                     in identifiers]
    csv_abs_filepaths = [csv_dir + os.sep + filename for filename in csv_filenames]
    csv_filelinks = [csv_dir.split(os.sep)[-1] + '/' + filename for filename in
                     csv_filenames]

    return csv_abs_filepaths, csv_filelinks


def csv_strings(csv_abs_filepaths, csv_filelinks, compact):
    """
    Creates a list of strings, one string for each chart. The strings are
        * either the 'links' to csv files, to work as reference inside the html file (like
          tables/processor_processor_busy, tables/aggregate_total_transfers...)
        * or the plain contents of the corresponding csv files, if the compact command line option
          is set
    The strings are made for writing to the html file.
    :param csv_abs_filepaths: A list of paths to the csv files.
    :param csv_filelinks: A list of the file 'links' to the same csv files. They are called links
    to be distinguished from the absolute or relative paths. More specific, they actually are
    paths, but seen relatively from the html location. Furthermore, their seperators are always /,
    even under windows machines, because the links are used to reference inside the html.
    :param compact: Boolean, which says whether command line option 'compact' is set or not. If
    True, function will return the csv_filelinks, if False, function will return the csv contents.
    :return: List of strings.
    """
    if compact:
        csv_content_list = []
        for path in csv_abs_filepaths:
            with open(path, 'r') as csv:
                csv_content_list += [csv.read()]
        return csv_content_list

    return csv_filelinks

