"""
Contains the class Table.
"""
from collections import defaultdict


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

    def get_rows(self, instance_set, number_of_iterations):
        """
        Simplifies the data structure into lists of table content equating table rows.
        :param instance_set: A Set containing all instance names (column names) occurring in the
        table.
        :param number_of_iterations: An Integer describing the number of rows, the table should
        have.
        :return: A list containing all column headers and a list of list, which is a list of
        rows, containing the table values. The order of the values equates the order of the headers.
        """
        value_rows = []
        header_row = []
        for instance in instance_set:
            header_row.append(instance)

        for iteration in range(1, number_of_iterations+1):
            iteration_dict = self.outer_dict[iteration]
            row = []
            for header in header_row:
                if header in iteration_dict:
                    row.append(iteration_dict[header])
                else:
                    row.append(' ')
                    print('Value for ' + str(header) + ' in iteration ' + str(iteration)
                          + ' is missing!')
            value_rows.append(row)
        return header_row, value_rows
