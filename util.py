"""
Provides some functions other modules may use.
"""
import os
from orderedset import OrderedSet
from table import Table
import constants

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


def get_month_number(month_string):
    """
    Find the corresponding month number to a simple month string
    :param month_string: String describing a month's shortcut, three letters long, first letter
    upper case.
    :return: The corresponding month number
    """
    return {
        'Jan': 1,
        'Feb': 2,
        'Mar': 3,
        'Apr': 4,
        'May': 5,
        'Jun': 6,
        'Jul': 7,
        'Aug': 8,
        'Sep': 9,
        'Oct': 10,
        'Nov': 11,
        'Dec': 12
    }[month_string]


def inner_ord_set_insertion(outer_list, index, item):
    """
    Inserts an item into a list of OrderedDicts. Inserts the item in the OrderedDict at the place of
    index. Is index bigger than the number of existing OrderedDicts, new OrderedDicts inside the
    list will be created.
    :param outer_list: The list of OrderedDicts you want to insert an item in.
    :param index: The OrderedDict's number, in which the item should be inserted in.
    :param item: The item you want insert.
    :return: None
    """
    if len(outer_list) <= index:
        missing_entries = index + 1 - len(outer_list)
        for _ in range(missing_entries):
            outer_list.append(OrderedSet())

    outer_list[index].add(item)


def tablelist_insertion(tablelist, list_index, iteration, instance, item):
    """
    Inserts a table item into a specific table in a list of tables. If the list index is bigger
    than the number of table elements in the list, table elements will be created.
    :param tablelist: A list of tables. The function will insert the item in one of those.
    :param list_index: The table's index in tablelist, you want to insert your item in.
    :param iteration: The number of iteration, your item belongs to - is needed to arrange
    elements inside one table.
    :param instance: The name as string of the instance, your item (which should be a value for
    this instance) belongs to - is needed to arrange
    elements inside one table.
    :param item: The table value you want to insert. It's related to a specific time and object
    instance, therefore it is the basis for a single measuring point in final charts.
    """
    if len(tablelist) <= list_index:
        missing_entries = list_index + 1 - len(tablelist)
        for _ in range(missing_entries):
            tablelist.append(Table())

    tablelist[list_index].insert(iteration, instance, item)


def empty_directory(preferred_directory_path):
    """
    Creates a directory which doesn't exist yet with a path, as close as possible to the
    preferred path.
    :param preferred_directory_path: The path you want to have the directory at.
    :return: The directory's name created actually.
    """
    directory_name = preferred_directory_path

    if os.path.exists(directory_name):
        i = 1
        while os.path.exists(directory_name):
            directory_name = preferred_directory_path + str(i)
            i += 1

    os.makedirs(directory_name)
    return directory_name


def get_units(per_iteration_requests):
    """
    Gets all units from a per_iteration_request dict.
    :param per_iteration_requests: A data structure carrying all requests for data, the tool is going
    to collect once per iteration. It's an OrderedDict of lists which contains all requested 
    object types mapped to the relating aspects and units which the tool should create graphs for.
    :return: A list of all units.
    """
    unit_list = []
    for object_type in per_iteration_requests:
        for request_tuple in per_iteration_requests.get(object_type):
            unit = request_tuple[1]
            unit_list.append(unit)
    return unit_list


def get_titles(per_iteration_requests):
    """
    Generates proper titles for charts.
    :param per_iteration_requests: A data structure carrying all requests for data, the tool is going
    to collect once per iteration. It's an OrderedDict of lists which contains all requested 
    object types mapped to the relating aspects and units which the tool should create graphs for.
    :return: A list of chart titles, relating on the given per_iteration_requests.
    """
    title_list = []
    for object_type in per_iteration_requests:
        for request_tuple in per_iteration_requests.get(object_type):
            aspect = request_tuple[0]
            title_list.append(object_type + ':' + aspect)
    return title_list


def get_object_ids(per_iteration_requests):
    """
    Gets all object IDs from a per_iteration_request.
    :param per_iteration_requests: A data structure carrying all requests for data, the tool is going
    to collect once per iteration. It's an OrderedDict of lists which contains all requested 
    object types mapped to the relating aspects and units which the tool should create graphs for.
    :return: A list of all object IDs.
    """
    id_list = []
    for object_type in per_iteration_requests:
        for request_tuple in per_iteration_requests.get(object_type):
            aspect = request_tuple[0]
            id_list.append(object_type + '_' + aspect)
    return id_list


def get_csv_file_names(per_iteration_requests):
    """
    Generates proper names for CSV files containing a selection of PerfStat Data.
    :param per_iteration_requests: A data structure carrying all requests for data, the tool is going
    to collect once per iteration. It's an OrderedDict of lists which contains all requested 
    object types mapped to the relating aspects and units which the tool should create graphs for.
    :return: A list of csv file names, relating on the given per_iteration_request.
    """
    name_list = []
    for object_type in per_iteration_requests:
        for request_tuple in per_iteration_requests.get(object_type):
            aspect = request_tuple[0]
            name_list.append(object_type + '_' + aspect +
                             constants.CSV_FILE_ENDING)
    return name_list
