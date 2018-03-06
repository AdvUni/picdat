import logging
import xml.etree.ElementTree as ET
from xml_mode.xml_item import XmlItem
from xml_mode.xml_container import XmlContainer

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


def read_data(data_file, info_file):
    container = XmlContainer()
    elem_dict = {}

    for _, elem in ET.iterparse(data_file):
        tag = elem.tag.split('}', 1)[1]
        # print ('tag : %s, content: %s' % (elem.tag.split('}', 1)[1], elem.text))
        # elem.clear()

        if tag == 'ROW':
            container.add_item(XmlItem(elem_dict))
            elem_dict = {}
        else:
            elem_dict[tag] = elem.text

        elem.clear()

    logging.debug(container.tables)

    return container.get_flat_tables(), container.build_identifier_dict()
