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
    an iteration or statit number (equates row) to an inner dict, each inner dict maps an 
    instance/disk name (equates table column) to a specific table value. So each table value has 
    a determined row and column.
    """

    def __init__(self):
        self.outer_dict = defaultdict(dict)

    def __str__(self):
        return str(self.outer_dict)

    def insert(self, row, column, item):
        """
        Inserts an value dependably into a specific place in the Table.
        :param row: Number of the iteration/statit, the value belongs to (equates table row).
        :param column: Name of the instance/disk, the value belongs to (equates table column).
        :param item: Value you want to insert.
        :return: None.
        """
        if row not in self.outer_dict:
            inner_dict = {column: item}
            self.outer_dict[row] = inner_dict
        else:
            inner_dict = self.outer_dict[row]
            if column not in inner_dict:
                inner_dict[column] = item
            else:
                self.outer_dict[row][column] = item

    def flatten(self, column_names, timestamps, offset):
        """
        Simplifies the data structure into lists of table content equating table rows.
        :param column_names: A Set containing all instance/disk names (column names) occurring in
        the table.
        :param timestamps: A list of datetime objects, marking the beginnings of
        iterations/statits. They'll be the table's first column. If this argument is None,
        function will replace timestamps with a simple range of numbers.
        :return: A list containing all column headers and a list of list, which is a list of
        rows, containing the table values. The order of the values equates the order of the headers.
        """
        rownames = timestamps
        if timestamps is None:
            rownames = list(range(len(self.outer_dict)))

        value_rows = []
        header_row = []
        for instance in column_names:
            header_row.append(instance)

        for row in range(len(rownames)):
            row_dict = self.outer_dict[row + offset]
            rowname = rownames[row]
            value_row = [str(rowname)]
            for header in header_row:
                if header in row_dict:
                    value_row.append(row_dict[header])
                else:
                    value_row.append(' ')
                    print('Value for ' + str(header) + ' is missing! (' + str(rowname) + ')')
            value_rows.append(value_row)

        return header_row, value_rows
