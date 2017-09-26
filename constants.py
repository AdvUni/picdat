"""
Constants
"""
import datetime
from os import sep

import logging

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


# String to print together with the program name if user uses command line option --help or -h or
# any not recognized options:
HELP = '''
usage: %s [--help] [--inputfile "input"] [--outputdir "output"] [--debug "level"]
    --help, -h: prints this message
    --inputfile "input", -i "input": input is the path to some PerfStat output. Should be a 
                                     folder, a .zip folder or a .data file.
    --outputdir "output", -o "output": output is the directory's path, where this program puts its 
                                       results. If there is no directory existing yet under this 
                                       path, one would be created. If there already are some 
                                       PicDat results, they might be overwritten.
    --debug "level", -d "level": level should be inside debug, info, warning, error, critical. It 
                                 describes the filtering level of command line output during 
                                 running this program (default is "info").
'''


# this log level is used, if the user didn't specify one:
DEFAULT_LOG_LEVEL = logging.INFO

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
STATIT_CHART_TITLE = 'statit%sdisk_statistics'

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

# this is the expected number of columns in statit blocks:
STATIT_COLUMNS = 18

# proportions of the html charts in px:
CHARTS_HEIGHT = 600
CHARTS_WIDTH = 900
