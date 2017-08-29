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


DEFAULT_PERFSTAT_OUTPUT_FILE = 'output.data'
DEFAULT_DIRECTORY_NAME = 'results'
CSV_FILE_ENDING = '_graph_values.csv'

HTML_FILENAME = 'graphs.html'
HTML_HEAD_TEMPLATE = 'graph_html_head_template.txt'

DYGRAPHS_JS_SRC = 'dygraphs/dygraph.js'
DYGRAPHS_CSS_SRC = 'dygraphs/dygraph.css'

X_LABEL = 'time'

SELECT_ALL_FCT = """
    function selectAll(button, chart, name) {
        var checkboxes = document.getElementsByName(name);
        for (var i = 0, n = checkboxes.length; i < n; i++) {
            checkboxes[i].checked = true;
            chart.setVisibility(i, true);
        }
    }
"""

DESELECT_ALL_FCT = """
function deselectAll(button, chart, name) {
        var checkboxes = document.getElementsByName(name);
        for (var i = 0, n = checkboxes.length; i < n; i++) {
            checkboxes[i].checked = false;
            chart.setVisibility(i, false);
        }
    }
"""
