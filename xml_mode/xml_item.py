'''

'''
import logging

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


class XmlItem:
    '''
    classdocs
    '''

    def __init__(self, content_dict):
        """
        :param content_dict: bla
        """
        try:
            self.timestamp = content_dict['timestamp']
            self.object = content_dict['object']
            self.instance = content_dict['instance']
            self.instance_uuid = content_dict['instance-uuid']
            self.counter = content_dict['counter']
            self.value = content_dict['value']
        except(KeyError):
            logging.error('Error with parsing xml element')

    def __repr__(self):
        return ('''timestamp:     %s
object:        %s
instance:      %s
instance-uuid: %s
counter:       %s
value:         %s'''
                % (self.timestamp, self.object, self.instance, self.instance_uuid, self.counter, self.value))
