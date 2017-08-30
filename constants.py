"""
Constants
"""

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


# program uses this path for it's analyse if user's input for that is empty:
DEFAULT_PERFSTAT_OUTPUT_FILE = 'output.data'

# program saves it's results in a directory named like that (might have an additional number):
DEFAULT_DIRECTORY_NAME = 'results'

# program names csv files with the name of the chart they belong to and the following ending:
CSV_FILE_ENDING = '_graph_values.csv'

# program names html file inside the result directory like this:
HTML_FILENAME = 'graphs.html'

# this is the path to the text file, the program uses as template to create the html head:
HTML_HEAD_TEMPLATE = 'graph_html_head_template.txt'

# these are the paths to the dygraph files, the html document needs to show it's charts:
DYGRAPHS_JS_SRC = 'dygraphs/dygraph.js'
DYGRAPHS_CSS_SRC = 'dygraphs/dygraph.css'

# this is the label showed on the x-axis in each chart:
X_LABEL = 'time'

# this is the number of checkboxes under a chart showed in one row.
COLUMN_NUMBER_OF_CHECKBOXES = 4

# this is the string sitting inside all checkboxes' IDs.
CHECKBOX_ID_SPLITTER = '_checkbox'

# this is the javaScript function which is responsible for showing all graphs in one chart at
# once; the program needs to write this string in the html document:
SELECT_ALL_FCT = '''
    function selectAll(button, chart, name) {
        var checkboxes = document.getElementsByName(name);
        for (var i = 0, n = checkboxes.length; i < n; i++) {
            checkboxes[i].checked = true;
            chart.setVisibility(i, true);
        }
    }
'''

# this is the javaScript function which is responsible for hiding all graphs in one chart at
# once; the program needs to write this string in the html document:
DESELECT_ALL_FCT = '''
function deselectAll(button, chart, name) {
        var checkboxes = document.getElementsByName(name);
        for (var i = 0, n = checkboxes.length; i < n; i++) {
            checkboxes[i].checked = false;
            chart.setVisibility(i, false);
        }
    }
'''
