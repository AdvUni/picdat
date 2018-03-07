"""
Contains the class Table.
"""
import logging
from collections import defaultdict

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


class Table:
    """
    This is a data structure to represent table content. It's a dict of dicts; each outer dict maps
    a row name to an inner dict, each inner dict maps an column name (equates table column) to a
    specific table value. So each table value has a determined row and column.
    """

    def __init__(self):
        self.outer_dict = defaultdict(dict)

    def __repr__(self):
        return str(self.outer_dict)

    def insert(self, row, column, item):
        """
        Inserts an value dependably into a specific place in the Table. If this table spot is
        already filled, the value will be overwritten.
        :param row: Name of the table row, the value belongs to.
        :param column: Name of the table column, the value belongs to.
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

    def get_item(self, row, column):
        """
        Returns an item from the table.
        :param row: The table's row, the item should be from
        :param column: The table's column, the item should be from
        :return: The item which is stored for row and column
        :raises IndexError, KeyError: If the table hasn't any item at selected row and column, one
        of those errors will occur
        """
        return self.outer_dict[row][column]

    def is_empty(self):
        """
        Checks whether the table is empty.
        :return: Boolean, whether table is empty or not.
        """
        return len(self.outer_dict) == 0

    def sort_columns_by_relevance(self):
        """
        Generates a list of all column names the table has. They'll be sorted by the sum of their
        values across all rows.
        :return: A list of all column names.
        """
        try:
            value_dict = {}
            for _, inner_dict in self.outer_dict.items():
                for column_name, value in inner_dict.items():
                    try:
                        if column_name in value_dict:
                            value_dict[column_name] += float(value)
                        else:
                            value_dict[column_name] = float(value)
                    except ValueError:
                        logging.warning('Found value, which is not convertible to float: %s - '
                                        '%s', column_name, value)
                        raise
            logging.debug('value dict: %s', value_dict)
            return sorted(value_dict, key=value_dict.get, reverse=True)
        except ValueError:
            logging.error('Was not able to sort columns by relevance. Sorting them by name '
                          'instead.')

            column_names = set()
            for _, inner_dict in self.outer_dict.items():
                for column_name in inner_dict:
                    column_names.add(column_name)

            return sorted(column_names)

    def flatten(self, x_label, sort_columns_by_name):
        """
        Simplifies the data structure into a nestet list.
        :param x_label: A String which should be in the upper left corner of the table. It's the
        label for the first table column naming the rows.
        :param sort_columns_by_name: If True, the columns of the flattened table will be sorted
        alphanumerically, otherwise method sorts them by relevance.
        :return: A nested list: Each inner list holds the values of one row in the table,
        the outer list holds all rows
        """
        row_names = set()
        column_names = set()
        for row_name, inner_dict in self.outer_dict.items():
            row_names.add(row_name)
            for column_name in inner_dict:
                column_names.add(column_name)

        if sort_columns_by_name:
            header_row = sorted(column_names)
        else:
            header_row = self.sort_columns_by_relevance()

        value_rows = []
        for row in sorted(row_names):
            row_dict = self.outer_dict[row]
            value_row = [str(row)]
            for column in header_row:
                if column in row_dict:
                    value_row.append(row_dict[column])
                else:
                    value_row.append(' ')
                    logging.info('Gap in table: Value is missing in row %s, column %s',
                                 str(row), column)
            value_rows.append(value_row)

        header_row.insert(0, x_label)

        logging.debug(value_rows)
        return [header_row] + value_rows
