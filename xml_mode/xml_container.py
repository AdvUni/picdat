'''

'''
from general.table import Table

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

REQUESTS = [('aggregate', 'total_transfers'), ('processor', 'processor_busy'), ('volume', 'total_ops'), ('volume',
                                                                                                         'avg_latency'), ('volume', 'read_data'), ('lun', 'total_ops'), ('lun', 'avg_latency'), ('lun', 'read_data')]


class XmlContainer:
    '''
    classdocs
    '''

    def __init__(self):
        '''
        Constructor
        '''
        self.object_types = {request[0] for request in REQUESTS}
        self.tables = {}
        for request in REQUESTS:
            self.tables[request] = Table()

    def add_item(self, xml_item):
        if xml_item.object in self.object_types:
            if (xml_item.object, xml_item.counter) in REQUESTS:
                self.tables[(xml_item.object, xml_item.counter)].insert(
                    xml_item.timestamp, xml_item.instance, xml_item.value)

    def get_flat_tables(self):

        return [(self.tables[request]).flatten('time', True) for request in REQUESTS]

    def get_csv_filenames(self):
        return [object_type + '_' + aspect + '.csv' for (object_type, aspect) in REQUESTS]

    def get_units(self):
        # TODO
        return ['someunit' for _ in REQUESTS]

    def get_x_labels(self):
        return ['time' for _ in REQUESTS]

    def get_object_ids(self):
        return [object_type + '_' + aspect for (object_type, aspect) in REQUESTS]

    def get_barchart_booleans(self):
        return ['false' for _ in REQUESTS]

    def get_titles(self):
        return ['sometitle' for _ in REQUESTS]

    def build_identifier_dict(self):
        return {'titles': self.get_titles(), 'units': self.get_units(), 'x_labels': self.get_x_labels(),
                'object_ids': self.get_object_ids(), 'barchart_booleans': self.get_barchart_booleans(), 'csv_names': self.get_csv_filenames()}
