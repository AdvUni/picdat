"""
This module contains the basis for all search keys of PicDat. Each request data structure must be
handled differently an will lead into one ore more charts.
"""
from collections import OrderedDict

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


# These search keys will match (at most) once in each iteration. Data collected about these
# requests will be shown in four charts: One for each of aggregate, processor, volume and lun.
# About the data structure: It's an OrderedDict of lists which contains all requested object
# types mapped to the relating aspects and units which the tool should create graphs for.
PER_ITERATION_REQUESTS = OrderedDict([
    ('aggregate', [('total_transfers', '/s')]),
    ('processor', [('processor_busy', '%')]),
    ('volume', [('total_ops', '/s'), ('avg_latency', 'us'), ('read_data', 'b/s')]),
    ('lun', [('total_ops', '/s'), ('avg_latency', 'ms'), ('read_data', 'b/s'),
             ('read_align_histo', '%')])
])

# These search keys will match many times inside sysstat_x_1sec blocks. They all belong to unit
# %. Data collected about these requests will be shown in one chart together.
# About the data structure: A list of tuples. Each tuple contains the name of a measurement in
# the first place and an additional identifier, which appears in the second sysstat header line,
# in the second place.
SYSSTAT_PERCENT_REQUESTS = [('CPU', ' '), ('Disk', 'util'), ('HDD', 'util'), ('SSD', 'util')]

SYSSTAT_PERCENT_UNIT = '%'

# These search keys will match many times inside sysstat_x_1sec blocks. They all belong to unit
# kB/s, but PicDat will convert the values to MB/s for better readability. Data collected about
# these requests will be shown in one chart together.
# About the data structure: A list of tuples. Each tuple contains the name of a measurement in
# the first place. In the second place is another tuple, containing two parameters, e.g. 'read'
# and 'write'.
SYSSTAT_MBS_REQUESTS = [('Net', ('in', 'out')), ('FCP', ('in', 'out')), ('Disk', ('read', 'write')),
                        ('HDD', ('read', 'write')), ('SSD', ('read', 'write'))]
SYSSTAT_MBS_UNIT = 'MB/s'

# These search keys will match many times inside sysstat_x_1sec blocks. They values for them
# haven't any unit; they're absolute. Data collected about this requests will be shown in one
# chart together.
SYSSTAT_IOPS_REQUESTS = ['NFS', 'CIFS', 'FCP', 'iSCSI']

SYSSTAT_NO_UNIT = ' '

STATIT_DISK_STAT_UNIT = '%'
