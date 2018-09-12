"""
This module is for reading hdf5 performance files. It holds an Hdf5Container
object which stores all collected data.
"""

import logging
try:
    import tables as pytable
except ImportError:
    pyables = None
    print('Warning: Module tables (PyTable) is not installed. PicDat won\'t be able to read '
          'hdf5 files. If you try to run PicDat in asup hdf5 mode, it will crash. With PerfStats '
          'or asup xml files, everything is fine.')
from asup_mode.hdf5_container import Hdf5Container

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

def read_hdf5(asup_hdf5_file, sort_columns_by_name):
    """
    This function reads a performance file in hdf5 format. It holds a Hdf5Container object to store
    all collected information.
    :param asup_hdf5_files: path to an .h5 file which contains performance data.
    :return: all chart data in tablelist format; ready to be written into csv tables. Additionally
    an identifier dict, which contains all required meta data about charts, labels or file names.
    """
    container = Hdf5Container()
    logging.info('Read data file(s)...')

    with pytable.open_file(asup_hdf5_file, 'r') as hdf5:
        for hdf5_table in hdf5.walk_nodes('/', 'Table'):
            container.search_hdf5(hdf5_table)
    
    # container.do_unit_conversions()

    return container.get_flat_tables(sort_columns_by_name), container.build_label_dict()