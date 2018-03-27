import logging
import tables as pytable
from asup_mode.hdf5_container import Hdf5Container


def read_hdf5(hdf5_file, sort_columns_by_name):
    container = Hdf5Container()
    logging.info('Read data file(s)...')

    with pytable.open_file(hdf5_file, 'r') as hdf5:
        for hdf5_table in hdf5.walk_nodes('/', 'Table'):
            container.search_hdf5(hdf5_table)
    
    # container.do_unit_conversions()

    return container.get_flat_tables(sort_columns_by_name), container.build_label_dict()
