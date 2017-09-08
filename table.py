"""
Contains the class Table.
"""
from collections import defaultdict

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


class Table:
    """
    This is a data structure to represent table content. It's a dict of dicts; each outer dict maps
    an iteration (equates row) to an inner dict, each inner dict maps an instance (equates table
    column) to a specific table value. So each table value has a determined row and column.
    """

    def __init__(self):
        self.outer_dict = defaultdict(dict)

    def __str__(self):
        return str(self.outer_dict)

    def insert(self, iteration, instance, item):
        """
        Inserts an value dependably into a specific place in the Table.
        :param iteration: Number of the iteration, the value belongs to (equates table row).
        :param instance: Name of the instance, the value belongs to (equates table column).
        :param item: Value you want to insert.
        :return: None.
        """
        if iteration not in self.outer_dict:
            inner_dict = {instance: item}
            self.outer_dict[iteration] = inner_dict
        else:
            inner_dict = self.outer_dict[iteration]
            if instance not in inner_dict:
                inner_dict[instance] = item
            else:
                self.outer_dict[iteration][instance] = item

    def get_rows(self, instance_set, iteration_timestamps):
        """
        Simplifies the data structure into lists of table content equating table rows.
        :param instance_set: A Set containing all instance names (column names) occurring in the
        table.
        :param iteration_timestamps: A list of datetime objects, marking the beginnings of
        iteration. They'll be the table's first column.
        :return: A list containing all column headers and a list of list, which is a list of
        rows, containing the table values. The order of the values equates the order of the headers.
        """
        value_rows = []
        header_row = []
        for instance in instance_set:
            header_row.append(instance)

        for iteration in range(len(iteration_timestamps)):
            iteration_dict = self.outer_dict[iteration + 1]
            row = [str(iteration_timestamps[iteration])]
            for header in header_row:
                if header in iteration_dict:
                    row.append(iteration_dict[header])
                else:
                    row.append(' ')
                    print('Value for ' + str(header) + ' in iteration ' + str(iteration + 1)
                          + ' is missing!')
            value_rows.append(row)

        return header_row, value_rows
