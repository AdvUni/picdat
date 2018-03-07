"""
Constants used within perfstat mode
"""
import datetime

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


# timedelta object describing one second. The data_collector needs it to count up the time to
# adress sysstat_1sec values correctly.
ONE_SECOND = datetime.timedelta(seconds=1)

DEFAULT_TIMESTAMP = datetime.datetime(2017, 1, 1)

# the standard string to name charts about the sysstat_x_1sec block:
SYSSTAT_CHART_TITLE = 'sysstat_x_1sec'

# the standard string to name the chart about the statit block:
STATIT_CHART_TITLE = 'statit%sdisk_statistics'

# this is the expected number of columns in statit blocks:
STATIT_COLUMNS = 18
