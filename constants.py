"""
Constants
"""
import datetime
from os import sep

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


# timedelta object describing one second. The data_collector needs it to count up the time to
# adress sysstat_1sec values correctly.
ONE_SECOND = datetime.timedelta(seconds=1)

DEFAULT_TIMESTAMP = datetime.datetime(2017, 1, 1)

# program uses this path for it's analysis if user's input for that is empty:
DEFAULT_PERFSTAT_OUTPUT_FILE = 'output.data'

# program saves its results in a directory named like that (might have an additional number):
DEFAULT_DIRECTORY_NAME = 'results'

# program names csv files with the name of the chart they belong to, and the following ending:
CSV_FILE_ENDING = '_chart_values.csv'

# program names html file inside the result directory like this:
HTML_FILENAME = 'charts'
HTML_ENDING = '.html'

# the standard string to name charts about the sysstat_x_1sec block:
SYSSTAT_CHART_TITLE = 'sysstat_x_1sec'

# the standard string to name the chart about the statit block:
STATIT_CHART_TITLE = 'statit_disk_statistics'

# this is the path to the text file the program uses as template to create the html head:
HTML_HEAD_TEMPLATE = 'html_template.txt'

# these are the paths to the dygraph files the html document needs to show its charts:
DYGRAPHS_JS_SRC = 'dygraphs' + sep + 'dygraph.js'
DYGRAPHS_CSS_SRC = 'dygraphs' + sep + 'dygraph.css'

# this is the label showed on the x-axis in each chart:
X_LABEL = 'time'

# this is the number of checkboxes under a chart shown in one row.
COLUMN_NUMBER_OF_CHECKBOXES = 4

# this is the string sitting inside all checkboxes' IDs.
CHECKBOX_ID_SPLITTER = '_checkbox'

# this is the html class name of all div elements which show legend content:
LEGEND_DIV_CLASS_NAME = 'legend-div'

# this is the html class name of all div elements which contain dygraph elements:
CHART_DIV_CLASS_NAME = 'chart-div'

# this is the javaScript function which is responsible for showing all graphs in one chart at
# once; the program needs to write this string in the html document:

# proportions of the html charts in px:
CHARTS_HEIGHT = 600
CHARTS_WIDTH = 900
