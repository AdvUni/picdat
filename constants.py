"""
Constants
"""

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