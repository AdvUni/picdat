import logging

try:
    import ijson
except ImportError:
    ijson = None
    print('Warning: Module ijson is not installed. PicDat won\'t be able to parse '
          'json files. If you try to run PicDat in asup json mode, it will crash. With PerfStats '
          'or asup xml files, everything is fine.')

from asup_mode.json_container import JsonContainer

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

def read_json(asup_json_files, sort_columns_by_name):
    container = JsonContainer()
    logging.info('Read data file(s)...')
    
    # initialise variables to write cluster and node names to
    cluster_and_node = None
    
    for file in asup_json_files:
        with open (file, 'r') as json_file:
            logging.info("Read file %s", file)
            iterjson = ijson.items(json_file, 'item')
            
            # get cluster and node name from the first element of each file
            first_item = next(iterjson)
            if not cluster_and_node:
                cluster_and_node = first_item['cluster_name'], first_item['node_name']
            else:
                if cluster_and_node != (first_item['cluster_name'], first_item['node_name']):
                    logging.error("inhomogeneous data: Different files in your input belong to different clusters/nodes. PicDat output will probably not make much sense.")
            
            # read data (first item and all others)
            container.add_data(first_item)
            for item in iterjson:
                container.add_data(item)
    
    container.do_unit_conversions()
    
    return container.get_flat_tables(sort_columns_by_name), container.build_lable_dict(), cluster_and_node
                
        